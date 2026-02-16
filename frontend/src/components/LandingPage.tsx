import { motion } from "framer-motion";
import { Activity, Compass, Rocket, MessageSquare } from "lucide-react";

interface Props {
  onModeSelect: (query?: string) => void;
}

const MODES = [
  {
    icon: Activity,
    badge: "W&B MONITOR",
    title: "Monitor a W&B Run",
    description: "Check training health, detect anomalies, get suggestions",
    query: "Analyze the health of my latest W&B run",
  },
  {
    icon: Compass,
    badge: "HF SCOUT",
    title: "Scout Models & Datasets",
    description: "Search HuggingFace for datasets and models",
    query: "Scout datasets and models for fine-tuning Qwen2.5-Coder-14B",
  },
  {
    icon: Rocket,
    badge: "LAUNCH TRAINING",
    title: "Launch a Training Job",
    description: "Configure and launch serverless fine-tuning",
    query: "Fine-tune Qwen2.5-Coder-14B on lilyzhng/uigen-ui-code-gen",
  },
  {
    icon: MessageSquare,
    badge: "FREE CHAT",
    title: "Just Chat",
    description: "Open-ended conversation about runs, data, workflow",
    query: undefined as string | undefined,
  },
];

const spring = { type: "spring" as const, stiffness: 80, damping: 15 };

export default function LandingPage({ onModeSelect }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6">
      <motion.div
        className="flex flex-col items-center max-w-2xl w-full"
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
      >
        {/* Logo */}
        <motion.img
          src="/logo.png"
          alt="SofaGenius"
          className="w-20 h-20 rounded-full object-cover shadow-sm mb-5"
          variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
          transition={spring}
        />

        {/* Heading */}
        <motion.h1
          className="font-serif text-4xl font-bold text-stone-900 mb-3"
          variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
          transition={spring}
        >
          SofaGenius
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          className="text-stone-500 text-sm text-center max-w-md mb-10"
          variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
          transition={spring}
        >
          Your best ideas come when you're relaxed,
          SofaGenius removes the grind so you can stay in creative mode.
        </motion.p>

        {/* Mode cards grid */}
        <div className="grid grid-cols-2 gap-4 w-full">
          {MODES.map((mode) => (
            <motion.button
              key={mode.badge}
              onClick={() => onModeSelect(mode.query)}
              className="flex flex-col items-start gap-3 p-5 bg-white rounded-xl border border-stone-200 shadow-sm text-left transition-all duration-200 hover:shadow-md hover:border-nobel-gold/50 cursor-pointer"
              variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
              transition={spring}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-nobel-cream">
                  <mode.icon size={18} className="text-nobel-gold" />
                </div>
                <span className="px-2.5 py-0.5 border border-nobel-gold text-nobel-gold text-[10px] tracking-[0.2em] uppercase font-bold rounded-full">
                  {mode.badge}
                </span>
              </div>
              <div>
                <h3 className="font-serif font-semibold text-stone-900 text-sm mb-1">
                  {mode.title}
                </h3>
                <p className="text-xs text-stone-500 leading-relaxed">
                  {mode.description}
                </p>
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
