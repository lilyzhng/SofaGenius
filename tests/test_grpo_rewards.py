"""Unit tests for GRPO reward functions and utilities.

Tests cover:
- _extract_tool_call utility (shared parser)
- 4 tool-calling reward functions (grpo_train.py)
- 5 generative UI reward functions (grpo_ui_train.py)
- dataset splitting utilities (dataset_utils.py)
- propose_training / launch_training card structure (modal_launcher.py)
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.modal_app.dataset_utils import (
    DEFAULT_EVAL_FRACTION,
    EVAL_SEED,
    MAX_EVAL,
    load_train_eval_split,
    should_skip_eval,
)
from backend.modal_app.grpo_train import (
    _extract_tool_call,
    correct_params_reward,
    correct_tool_reward,
    no_hallucination_reward,
    prepare_hermes_for_grpo,
    valid_json_reward,
)
from backend.modal_app.grpo_ui_train import (
    completeness_reward,
    interactivity_reward,
    length_penalty,
    prepare_ui_dataset,
    quote_balance_reward,
    validity_reward,
)


# ---------------------------------------------------------------------------
# Helper: wrap text in the completion format GRPOTrainer uses
# ---------------------------------------------------------------------------

def _comp(text: str) -> list[list[dict]]:
    """Wrap a string into the completions format: [[{"content": text}]]."""
    return [[{"content": text}]]


def _comps(*texts: str) -> list[list[dict]]:
    """Wrap multiple strings into completions format."""
    return [[{"content": t}] for t in texts]


# ===================================================================
# _extract_tool_call
# ===================================================================

class TestExtractToolCall:
    def test_valid_tool_call(self):
        text = '<tool_call>{"name": "get_weather", "arguments": {"city": "NYC"}}</tool_call>'
        result = _extract_tool_call(text)
        assert result is not None
        assert result["name"] == "get_weather"
        assert result["arguments"] == {"city": "NYC"}

    def test_tool_call_with_surrounding_text(self):
        text = 'I will call a tool.\n<tool_call>{"name": "search", "arguments": {"q": "test"}}</tool_call>\nDone.'
        result = _extract_tool_call(text)
        assert result is not None
        assert result["name"] == "search"

    def test_no_tool_call(self):
        assert _extract_tool_call("Hello, no tool call here.") is None

    def test_malformed_json(self):
        text = "<tool_call>{not valid json}</tool_call>"
        assert _extract_tool_call(text) is None

    def test_missing_name_field(self):
        text = '<tool_call>{"function": "foo", "arguments": {}}</tool_call>'
        assert _extract_tool_call(text) is None

    def test_missing_arguments_field(self):
        text = '<tool_call>{"name": "foo"}</tool_call>'
        assert _extract_tool_call(text) is None

    def test_empty_tool_call(self):
        text = "<tool_call></tool_call>"
        assert _extract_tool_call(text) is None

    def test_multiline_json(self):
        text = """<tool_call>
{
    "name": "calculate",
    "arguments": {
        "expression": "2+2"
    }
}
</tool_call>"""
        result = _extract_tool_call(text)
        assert result is not None
        assert result["name"] == "calculate"
        assert result["arguments"]["expression"] == "2+2"


# ===================================================================
# Tool-calling reward functions
# ===================================================================

class TestValidJsonReward:
    def test_valid(self):
        text = '<tool_call>{"name": "foo", "arguments": {"a": 1}}</tool_call>'
        assert valid_json_reward(_comp(text)) == [1.0]

    def test_invalid_no_tags(self):
        assert valid_json_reward(_comp("just plain text")) == [0.0]

    def test_invalid_bad_json(self):
        assert valid_json_reward(_comp("<tool_call>not json</tool_call>")) == [0.0]

    def test_batch(self):
        valid = '<tool_call>{"name": "a", "arguments": {}}</tool_call>'
        invalid = "no tool call"
        result = valid_json_reward(_comps(valid, invalid, valid))
        assert result == [1.0, 0.0, 1.0]

    def test_empty_completion(self):
        assert valid_json_reward([[]]) == [0.0]


class TestCorrectToolReward:
    def test_correct_name(self):
        text = '<tool_call>{"name": "get_weather", "arguments": {}}</tool_call>'
        gt = [json.dumps({"name": "get_weather", "arguments": {"city": "NYC"}})]
        assert correct_tool_reward(_comp(text), ground_truth=gt) == [1.0]

    def test_wrong_name(self):
        text = '<tool_call>{"name": "get_time", "arguments": {}}</tool_call>'
        gt = [json.dumps({"name": "get_weather", "arguments": {}})]
        assert correct_tool_reward(_comp(text), ground_truth=gt) == [0.0]

    def test_no_tool_call(self):
        gt = [json.dumps({"name": "foo", "arguments": {}})]
        assert correct_tool_reward(_comp("plain text"), ground_truth=gt) == [0.0]

    def test_no_ground_truth(self):
        text = '<tool_call>{"name": "foo", "arguments": {}}</tool_call>'
        assert correct_tool_reward(_comp(text)) == [0.0]


class TestCorrectParamsReward:
    def test_all_params_correct(self):
        text = '<tool_call>{"name": "f", "arguments": {"x": 1, "y": 2}}</tool_call>'
        gt = [json.dumps({"name": "f", "arguments": {"x": 1, "y": 2}})]
        assert correct_params_reward(_comp(text), ground_truth=gt) == [1.0]

    def test_partial_params(self):
        text = '<tool_call>{"name": "f", "arguments": {"x": 1, "y": 999}}</tool_call>'
        gt = [json.dumps({"name": "f", "arguments": {"x": 1, "y": 2}})]
        result = correct_params_reward(_comp(text), ground_truth=gt)
        assert result == [0.5]  # 1 out of 2 correct

    def test_no_params_expected_none_given(self):
        text = '<tool_call>{"name": "f", "arguments": {}}</tool_call>'
        gt = [json.dumps({"name": "f", "arguments": {}})]
        assert correct_params_reward(_comp(text), ground_truth=gt) == [1.0]

    def test_missing_all_params(self):
        text = '<tool_call>{"name": "f", "arguments": {}}</tool_call>'
        gt = [json.dumps({"name": "f", "arguments": {"x": 1, "y": 2}})]
        assert correct_params_reward(_comp(text), ground_truth=gt) == [0.0]

    def test_no_tool_call(self):
        gt = [json.dumps({"name": "f", "arguments": {"x": 1}})]
        assert correct_params_reward(_comp("no call"), ground_truth=gt) == [0.0]


class TestNoHallucinationReward:
    def test_valid_tool(self):
        text = '<tool_call>{"name": "search", "arguments": {}}</tool_call>'
        tools = [json.dumps(["search", "get_weather", "calculate"])]
        assert no_hallucination_reward(_comp(text), available_tools=tools) == [1.0]

    def test_hallucinated_tool(self):
        text = '<tool_call>{"name": "hack_system", "arguments": {}}</tool_call>'
        tools = [json.dumps(["search", "get_weather"])]
        assert no_hallucination_reward(_comp(text), available_tools=tools) == [-2.0]

    def test_no_tool_call(self):
        tools = [json.dumps(["search"])]
        assert no_hallucination_reward(_comp("no call"), available_tools=tools) == [0.0]

    def test_no_available_tools(self):
        text = '<tool_call>{"name": "foo", "arguments": {}}</tool_call>'
        assert no_hallucination_reward(_comp(text)) == [0.0]


# ===================================================================
# Generative UI reward functions
# ===================================================================

class TestCompletenessReward:
    def test_complete_jsx(self):
        text = "export default function App() { return <div>Hello</div> }"
        assert completeness_reward(_comp(text)) == [7.5]

    def test_complete_closing_div(self):
        text = "<div className='container'><p>Content</p></div>"
        assert completeness_reward(_comp(text)) == [7.5]

    def test_truncated(self):
        text = "function App() { return <div className="
        assert completeness_reward(_comp(text)) == [-15.0]

    def test_self_closing(self):
        text = "<input type='text' />"
        assert completeness_reward(_comp(text)) == [7.5]


class TestValidityReward:
    def test_all_balanced(self):
        text = "function foo() { return [1, 2, (3 + 4)]; }"
        assert validity_reward(_comp(text)) == [3.0]

    def test_unbalanced_braces(self):
        text = "function foo() { return [1, 2]; "
        result = validity_reward(_comp(text))
        assert result == [2.0]  # brackets and parens balanced, braces not

    def test_all_unbalanced(self):
        text = "{ [ ("
        assert validity_reward(_comp(text)) == [0.0]

    def test_empty_string(self):
        assert validity_reward(_comp("")) == [3.0]  # 0 == 0 for all


class TestInteractivityReward:
    def test_full_interactivity(self):
        text = """
        const [count, setCount] = useState(0);
        useEffect(() => {}, []);
        onClick={() => setCount(count + 1)}
        onChange={(e) => setValue(e.target.value)}
        onSubmit={handleSubmit}
        """
        assert interactivity_reward(_comp(text)) == [5.0]

    def test_no_interactivity(self):
        text = "<div>Static content</div>"
        assert interactivity_reward(_comp(text)) == [0.0]

    def test_partial_interactivity(self):
        text = "const [x, setX] = useState(0); onClick={() => setX(1)}"
        result = interactivity_reward(_comp(text))
        assert result == [2.0]  # useState + onClick

    def test_useeffect_only(self):
        text = "useEffect(() => { fetchData(); }, []);"
        assert interactivity_reward(_comp(text)) == [1.0]


class TestQuoteBalanceReward:
    def test_balanced(self):
        text = 'const x = "hello"; const y = \'world\';'
        assert quote_balance_reward(_comp(text)) == [2.0]

    def test_unbalanced_double(self):
        text = 'const x = "hello'
        result = quote_balance_reward(_comp(text))
        assert result[0] < 2.0  # at least double quotes unbalanced

    def test_empty(self):
        assert quote_balance_reward(_comp("")) == [2.0]


class TestLengthPenalty:
    def test_normal_length(self):
        text = "x" * 200
        assert length_penalty(_comp(text)) == [0.0]

    def test_too_short(self):
        text = "hi"
        assert length_penalty(_comp(text)) == [-5.0]

    def test_too_long(self):
        text = "x" * 9000
        assert length_penalty(_comp(text)) == [-2.0]

    def test_boundary_50(self):
        assert length_penalty(_comp("x" * 49)) == [-5.0]
        assert length_penalty(_comp("x" * 50)) == [0.0]


# ===================================================================
# Dataset splitting utilities
# ===================================================================

class TestShouldSkipEval:
    def test_max_steps_1(self):
        assert should_skip_eval({"max_steps": 1}) is True

    def test_tiny_train_size(self):
        assert should_skip_eval({"train_size": 2}) is True
        assert should_skip_eval({"train_size": 4}) is True

    def test_train_size_boundary(self):
        assert should_skip_eval({"train_size": 5}) is False

    def test_normal_exp(self):
        assert should_skip_eval({"max_steps": 50, "train_size": 100}) is False

    def test_prod_mode(self):
        assert should_skip_eval({"max_steps": 300}) is False

    def test_default_config(self):
        assert should_skip_eval({}) is False

    def test_max_steps_minus_1(self):
        assert should_skip_eval({"max_steps": -1}) is False

    def test_train_size_none(self):
        assert should_skip_eval({"train_size": None}) is False


class TestLoadTrainEvalSplit:
    """Test load_train_eval_split with mocked HF datasets."""

    def _make_fake_dataset(self, n):
        """Create a simple fake HF-like dataset."""
        from datasets import Dataset
        return Dataset.from_dict({"text": [f"sample_{i}" for i in range(n)]})

    @patch("datasets.get_dataset_split_names")
    @patch("datasets.load_dataset")
    def test_skip_eval_returns_none(self, mock_load, mock_splits):
        mock_load.return_value = self._make_fake_dataset(100)
        train, eval_ds = load_train_eval_split("test/ds", skip_eval=True)
        assert eval_ds is None
        assert len(train) == 100

    @patch("datasets.get_dataset_split_names")
    @patch("datasets.load_dataset")
    def test_uses_test_split_when_available(self, mock_load, mock_splits):
        mock_splits.return_value = ["train", "test"]
        train_ds = self._make_fake_dataset(100)
        test_ds = self._make_fake_dataset(20)
        mock_load.side_effect = [train_ds, test_ds]
        train, eval_ds = load_train_eval_split("test/ds")
        assert eval_ds is not None
        # Eval scaled to 10% of train (100) = 10, so 20 gets capped to 10
        assert len(eval_ds) == 10
        assert len(train) == 100

    @patch("datasets.get_dataset_split_names")
    @patch("datasets.load_dataset")
    def test_creates_split_when_no_test(self, mock_load, mock_splits):
        mock_splits.return_value = ["train"]
        mock_load.return_value = self._make_fake_dataset(100)
        train, eval_ds = load_train_eval_split("test/ds")
        assert eval_ds is not None
        # 100 total → 90 train, 10 eval from split. Eval cap = 10% of 90 = 9
        assert len(eval_ds) == 9
        assert len(train) == 90
        # No overlap
        train_texts = set(train["text"])
        eval_texts = set(eval_ds["text"])
        assert train_texts.isdisjoint(eval_texts)

    @patch("datasets.get_dataset_split_names")
    @patch("datasets.load_dataset")
    def test_caps_eval_at_max(self, mock_load, mock_splits):
        mock_splits.return_value = ["train", "test"]
        train_ds = self._make_fake_dataset(1000)
        test_ds = self._make_fake_dataset(500)
        mock_load.side_effect = [train_ds, test_ds]
        train, eval_ds = load_train_eval_split("test/ds")
        assert len(eval_ds) <= MAX_EVAL

    @patch("datasets.get_dataset_split_names")
    @patch("datasets.load_dataset")
    def test_max_train_samples(self, mock_load, mock_splits):
        mock_splits.return_value = ["train"]
        mock_load.return_value = self._make_fake_dataset(1000)
        train, eval_ds = load_train_eval_split("test/ds", max_train_samples=50)
        # Split from full 1000 first (900 train, 100 eval), cap train at 50,
        # then eval scaled to 10% of 50 = 5
        assert len(train) == 50
        assert len(eval_ds) == 5

    @patch("datasets.get_dataset_split_names")
    @patch("datasets.load_dataset")
    def test_split_is_deterministic(self, mock_load, mock_splits):
        """Same seed should produce same split."""
        mock_splits.return_value = ["train"]
        ds = self._make_fake_dataset(100)
        mock_load.return_value = ds
        _, eval1 = load_train_eval_split("test/ds")
        mock_load.return_value = ds
        _, eval2 = load_train_eval_split("test/ds")
        assert eval1["text"] == eval2["text"]


class TestPrepareHermesReturnsTuple:
    """Verify prepare_hermes_for_grpo returns (train, eval) tuple."""

    @patch("datasets.load_dataset")
    def test_returns_tuple_with_eval(self, mock_load):
        from datasets import Dataset
        # Create fake Hermes-format data
        rows = []
        for i in range(50):
            rows.append({
                "conversations": [
                    {"from": "human", "value": f"Call tool {i}"},
                    {"from": "gpt", "value": f'<tool_call>{{"name": "tool_{i}", "arguments": {{"x": {i}}}}}</tool_call>'},
                ],
                "tools": json.dumps([{"function": {"name": f"tool_{i}"}}]),
            })
        ds = Dataset.from_list(rows)
        mock_load.return_value = ds

        train, eval_ds = prepare_hermes_for_grpo(
            "test/ds", configs=("cfg",), max_samples=None, skip_eval=False,
        )
        assert isinstance(train, Dataset)
        assert isinstance(eval_ds, Dataset)
        assert len(train) + len(eval_ds) <= 50
        assert "prompt" in train.column_names
        assert "prompt" in eval_ds.column_names

    @patch("datasets.load_dataset")
    def test_returns_none_eval_when_skip(self, mock_load):
        from datasets import Dataset
        rows = [{
            "conversations": [
                {"from": "human", "value": "Call tool"},
                {"from": "gpt", "value": '<tool_call>{"name": "t", "arguments": {}}</tool_call>'},
            ],
            "tools": json.dumps([{"function": {"name": "t"}}]),
        }]
        mock_load.return_value = Dataset.from_list(rows)

        train, eval_ds = prepare_hermes_for_grpo(
            "test/ds", configs=("cfg",), max_samples=None, skip_eval=True,
        )
        assert eval_ds is None


class TestPrepareUiReturnsTuple:
    """Verify prepare_ui_dataset returns (train, eval) tuple."""

    @patch("datasets.get_dataset_split_names")
    @patch("datasets.load_dataset")
    def test_returns_tuple_with_eval(self, mock_load, mock_splits):
        from datasets import Dataset
        mock_splits.return_value = ["train"]
        rows = [{"text": f"# Task: Build component {i}\n```code```"} for i in range(50)]
        mock_load.return_value = Dataset.from_list(rows)

        train, eval_ds = prepare_ui_dataset("test/ds", max_samples=None, skip_eval=False)
        assert eval_ds is not None
        # 50 → 45 train, 5 from split. Eval capped to 10% of 45 = 4
        assert len(train) == 45
        assert len(eval_ds) == 4
        assert "prompt" in train.column_names

    @patch("datasets.get_dataset_split_names")
    @patch("datasets.load_dataset")
    def test_returns_none_eval_when_skip(self, mock_load, mock_splits):
        from datasets import Dataset
        mock_splits.return_value = ["train"]
        rows = [{"text": "# Task: test\ncode"}]
        mock_load.return_value = Dataset.from_list(rows)

        train, eval_ds = prepare_ui_dataset("test/ds", max_samples=None, skip_eval=True)
        assert eval_ds is None


# ===================================================================
# propose_training card structure
# ===================================================================

class TestProposeTraining:
    """Tests for the unified propose_training tool."""

    def test_grpo_overfit_card_structure(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="NousResearch/hermes-function-calling-v1",
            method="grpo",
            run_mode="overfit",
        ))
        assert result["card_type"] == "launch_card"
        assert result["launch_type"] == "grpo"
        assert result["status"] == "proposed"
        assert result["requires_approval"] is True
        assert result["config"]["method"] == "grpo"
        assert result["config"]["max_steps"] == 1
        assert result["config"]["num_generations"] == 4
        assert result["config"]["launch_type"] == "grpo"
        assert result["cost_estimate"]["gpu_type"] == "A100"
        assert result["cost_estimate"]["estimated_cost_usd"] >= 0

    def test_grpo_exp_card(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="NousResearch/hermes-function-calling-v1",
            method="grpo",
            run_mode="exp",
        ))
        assert result["config"]["max_steps"] == 50
        assert result["config"]["num_generations"] == 4
        assert result["config"]["train_size"] == 100

    def test_grpo_prod_card(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="NousResearch/hermes-function-calling-v1",
            method="grpo",
            run_mode="prod",
        ))
        assert result["config"]["max_steps"] == 300
        assert result["config"]["push_to_hub"] is True

    def test_grpo_custom_overrides(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="test/dataset",
            method="grpo",
            run_mode="overfit",
            learning_rate=1e-5,
            lora_r=16,
            num_generations=8,
        ))
        assert result["config"]["learning_rate"] == 1e-5
        assert result["config"]["lora_r"] == 16
        assert result["config"]["num_generations"] == 8

    def test_sft_overfit_card_structure(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="lilyzhng/uigen-ui-code-gen",
            method="sft",
            run_mode="overfit",
        ))
        assert result["card_type"] == "launch_card"
        assert result["launch_type"] == "finetune"
        assert result["status"] == "proposed"
        assert result["config"]["method"] == "sft"
        assert result["config"]["max_steps"] == 1
        assert result["config"]["batch_size"] == 1
        assert result["config"]["gradient_accumulation_steps"] == 8
        assert result["config"]["learning_rate"] == 2e-4

    def test_sft_prod_card(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="lilyzhng/uigen-ui-code-gen",
            method="sft",
            run_mode="prod",
        ))
        assert result["config"]["push_to_hub"] is True
        assert result["config"]["max_steps"] == -1

    def test_grpo_ui_generation_task_defaults(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="lilyzhng/uigen-ui-code-gen",
            method="grpo",
            run_mode="overfit",
            task_type="ui_generation",
        ))
        assert result["config"]["task_type"] == "ui_generation"
        assert result["config"]["max_completion_length"] == 2048
        assert result["config"]["wandb_project"] == "grpo-ui-gen"

    def test_grpo_tool_calling_defaults(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="NousResearch/hermes-function-calling-v1",
            method="grpo",
            run_mode="overfit",
            task_type="tool_calling",
        ))
        assert result["config"]["task_type"] == "tool_calling"
        assert result["config"]["max_completion_length"] == 512
        assert result["config"]["wandb_project"] == "grpo-tool-calling"

    def test_invalid_method_defaults_to_sft(self):
        from backend.tools.modal_launcher import propose_training

        result = json.loads(propose_training(
            dataset_name="test/ds",
            method="invalid",
            run_mode="overfit",
        ))
        assert result["config"]["method"] == "sft"


# ===================================================================
# launch_training dispatch logic
# ===================================================================

class TestLaunchTrainingDispatch:
    """Verify launch_training dispatches to the correct Modal function."""

    @patch("modal.Function")
    def test_sft_dispatches_to_run_finetune(self, mock_fn_cls):
        from backend.tools.modal_launcher import launch_training

        mock_fn = MagicMock()
        mock_call = MagicMock()
        mock_call.object_id = "call-123"
        mock_fn.spawn.return_value = mock_call
        mock_fn_cls.from_name.return_value = mock_fn

        config = {"method": "sft", "model_name": "Qwen/Qwen2.5-Coder-14B", "launch_type": "finetune"}
        result = json.loads(launch_training(json.dumps(config)))

        mock_fn_cls.from_name.assert_called_with("sofa-genius-launcher", "run_finetune")
        assert result["status"] == "running"

    @patch("modal.Function")
    def test_grpo_dispatches_to_run_grpo(self, mock_fn_cls):
        from backend.tools.modal_launcher import launch_training

        mock_fn = MagicMock()
        mock_call = MagicMock()
        mock_call.object_id = "call-456"
        mock_fn.spawn.return_value = mock_call
        mock_fn_cls.from_name.return_value = mock_fn

        config = {"method": "grpo", "model_name": "Qwen/Qwen2.5-Coder-14B", "launch_type": "grpo"}
        result = json.loads(launch_training(json.dumps(config)))

        mock_fn_cls.from_name.assert_called_with("sofa-genius-launcher", "run_grpo")
        assert result["status"] == "running"

    @patch("modal.Function")
    def test_backward_compat_infers_from_launch_type(self, mock_fn_cls):
        from backend.tools.modal_launcher import launch_training

        mock_fn = MagicMock()
        mock_call = MagicMock()
        mock_call.object_id = "call-789"
        mock_fn.spawn.return_value = mock_call
        mock_fn_cls.from_name.return_value = mock_fn

        # Old-style config without "method" key
        config = {"model_name": "Qwen/Qwen2.5-Coder-14B", "launch_type": "grpo"}
        result = json.loads(launch_training(json.dumps(config)))

        mock_fn_cls.from_name.assert_called_with("sofa-genius-launcher", "run_grpo")
        assert result["status"] == "running"


# ===================================================================
# Integration: tool summaries
# ===================================================================

class TestToolSummaries:
    def test_propose_training_sft_summary(self):
        from backend.agents.base import _summarize_tool_result
        card = {"config": {"method": "sft"}, "status": "proposed"}
        assert _summarize_tool_result("propose_training", json.dumps(card)) == "Fine-tuning job proposed"

    def test_propose_training_grpo_summary(self):
        from backend.agents.base import _summarize_tool_result
        card = {"config": {"method": "grpo"}, "status": "proposed"}
        assert _summarize_tool_result("propose_training", json.dumps(card)) == "GRPO job proposed"

    def test_launch_training_running_summary(self):
        from backend.agents.base import _summarize_tool_result
        card = {"config": {"method": "sft"}, "status": "running"}
        assert _summarize_tool_result("launch_training", json.dumps(card)) == "Fine-tuning job running"

    def test_launch_training_grpo_failed_summary(self):
        from backend.agents.base import _summarize_tool_result
        card = {"config": {"method": "grpo"}, "status": "failed"}
        assert _summarize_tool_result("launch_training", json.dumps(card)) == "GRPO job failed"

    def test_modify_and_propose_summary(self):
        from backend.agents.base import _summarize_tool_result
        card = {"config": {"method": "sft"}, "status": "proposed"}
        assert _summarize_tool_result("modify_and_propose", json.dumps(card)) == "Config updated, new proposal created"
