#!/bin/bash
set -ex

# =============================================================================
# APEX Professional Tasks — SkyRL + Harbor on Modal
#
# This script runs INSIDE the Modal container via SkyRL's Modal launcher.
# Data is on Modal volume at /root/data/apex-harbor-train/
#
# Launch from local machine:
#   # Prepare data first (one-time):
#   MODAL_GPU=A100:1 modal run examples/train_integrations/modal/main.py \
#     --command "pip install huggingface_hub && python -c \"
#       from huggingface_hub import snapshot_download
#       snapshot_download('lilyzhng/apex-harbor-train', repo_type='dataset', local_dir='/root/data/apex-harbor-train')
#     \""
#
#   # Sanity check (1 step):
#   MODAL_GPU=A100:4 MODAL_TIMEOUT=7200 modal run examples/train_integrations/modal/main.py \
#     --command "bash harbor_pipeline/scripts/run_apex_train.sh --trainer.max_steps=1"
#
#   # Full training:
#   MODAL_GPU=A100:4 MODAL_TIMEOUT=14400 modal run --detach examples/train_integrations/modal/main.py \
#     --command "bash harbor_pipeline/scripts/run_apex_train.sh"
# =============================================================================

#-----------------------
# Dataset setup
#-----------------------
# Data downloaded to Modal volume from lilyzhng/apex-harbor-train
TRAIN_DATA="['/root/data/apex-harbor-train']"

#-----------------------
# Directory setup
#-----------------------
RUN_NAME="${SKYRL_RUN_NAME:-apex-grpo-$(date +%m%d-%H%M)}"
TRIALS_DIR="/root/data/$RUN_NAME/trials_run"
CKPTS_DIR="/root/data/$RUN_NAME/ckpts"
EXPORTS_DIR="/root/data/$RUN_NAME/exports"
LOG_DIR="/tmp/skyrl-logs/$RUN_NAME"

#-----------------------
# Model
#-----------------------
MODEL="Qwen/Qwen3-Coder-30B-A3B-Instruct"
MODEL_SHORT="Qwen3-Coder-30B-A3B-Instruct"

#-----------------------
# Training setup
#-----------------------
MINI_BATCH_SIZE=8
MAX_MODEL_LEN=16384

# Dr. GRPO parameters
LOSS_REDUCTION="seq_mean_token_sum_norm"
GRPO_NORM_BY_STD=false
USE_KL_LOSS=false

# Harbor trial config (bundled with the repo)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRIAL_CONFIG="$SCRIPT_DIR/harbor_trial_config.yaml"

#-----------------------
# Infrastructure
#-----------------------
NUM_GPUS=4

# Rate limiting for Modal sandboxes
ENABLE_RATE_LIMITING=true
TRAJECTORIES_PER_SECOND=5
MAX_CONCURRENCY=32

# Start GPU watchdog in background (kills training if GPU idle >5 min)
bash "$SCRIPT_DIR/gpu_watchdog.sh" &
WATCHDOG_PID=$!
trap "kill $WATCHDOG_PID 2>/dev/null" EXIT

# Run SkyRL
uv run --isolated --extra fsdp --extra harbor -m examples.train_integrations.harbor.entrypoints.main_harbor \
  data.train_data=$TRAIN_DATA \
  trainer.policy.model.path=$MODEL \
  generator.inference_engine.served_model_name=$MODEL_SHORT \
  harbor_trial_config=$TRIAL_CONFIG \
  harbor_trial_config.trials_dir=$TRIALS_DIR \
  trainer.export_path=$EXPORTS_DIR \
  trainer.ckpt_path=$CKPTS_DIR \
  trainer.log_path=$LOG_DIR \
  trainer.algorithm.advantage_estimator=grpo \
  trainer.algorithm.loss_reduction=$LOSS_REDUCTION \
  trainer.algorithm.grpo_norm_by_std=$GRPO_NORM_BY_STD \
  trainer.algorithm.use_kl_loss=$USE_KL_LOSS \
  trainer.placement.colocate_all=true \
  trainer.strategy=fsdp2 \
  trainer.placement.policy_num_nodes=1 \
  trainer.placement.ref_num_nodes=1 \
  trainer.placement.policy_num_gpus_per_node=$NUM_GPUS \
  trainer.placement.ref_num_gpus_per_node=$NUM_GPUS \
  generator.inference_engine.num_engines=$NUM_GPUS \
  generator.inference_engine.tensor_parallel_size=1 \
  generator.inference_engine.engine_init_kwargs.max_model_len=$MAX_MODEL_LEN \
  generator.inference_engine.engine_init_kwargs.enable_log_requests=false \
  trainer.epochs=3 \
  trainer.eval_batch_size=32 \
  trainer.eval_before_train=true \
  trainer.eval_interval=10 \
  trainer.update_epochs_per_batch=1 \
  trainer.train_batch_size=$MINI_BATCH_SIZE \
  trainer.policy_mini_batch_size=$MINI_BATCH_SIZE \
  trainer.micro_forward_batch_size_per_gpu=1 \
  trainer.micro_train_batch_size_per_gpu=1 \
  trainer.ckpt_interval=5 \
  trainer.hf_save_interval=5 \
  trainer.algorithm.max_seq_len=$MAX_MODEL_LEN \
  trainer.policy.optimizer_config.lr=5.0e-6 \
  generator.n_samples_per_prompt=2 \
  generator.eval_n_samples_per_prompt=3 \
  generator.apply_overlong_filtering=true \
  generator.inference_engine.gpu_memory_utilization=0.5 \
  trainer.logger=wandb \
  trainer.project_name=apex-professional \
  trainer.run_name=$RUN_NAME \
  trainer.resume_mode=latest \
  generator.inference_engine.backend=vllm \
  generator.inference_engine.run_engines_locally=true \
  generator.inference_engine.weight_sync_backend=nccl \
  generator.inference_engine.async_engine=true \
  generator.batched=false \
  generator.inference_engine.enforce_eager=false \
  generator.inference_engine.enable_http_endpoint=true \
  generator.inference_engine.http_endpoint_host=127.0.0.1 \
  generator.inference_engine.http_endpoint_port=8000 \
  generator.rate_limit.enabled=$ENABLE_RATE_LIMITING \
  generator.rate_limit.trajectories_per_second=$TRAJECTORIES_PER_SECOND \
  generator.rate_limit.max_concurrency=$MAX_CONCURRENCY \
  "$@"
