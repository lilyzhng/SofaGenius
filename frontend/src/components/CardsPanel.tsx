import { AnimatePresence, motion } from "framer-motion";
import { BarChart2 } from "lucide-react";
import WandBHealthCard from "./WandBHealthCard";
import DataCard from "./DataCard";
import ScoutCard from "./ScoutCard";
import DraftPostCard from "./DraftPostCard";
import type { CardData } from "../types";

interface Props {
  cards: CardData[];
}

export default function CardsPanel({ cards }: Props) {
  if (cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <div className="w-16 h-16 rounded-full bg-nobel-cream-dark border border-stone-200 flex items-center justify-center mb-4">
          <BarChart2 size={24} className="text-stone-400" />
        </div>
        <p className="text-sm text-stone-400 max-w-xs">
          Cards will appear here when you ask me to analyze a W&B run or explore a dataset.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-4 py-6 space-y-4">
      <AnimatePresence mode="popLayout">
        {cards.map((card, i) => (
          <motion.div
            key={i}
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 80, damping: 15 }}
          >
            {card.card_type === "wandb_health" && (
              <WandBHealthCard card={card} />
            )}
            {card.card_type === "data_card" && (
              <DataCard card={card} />
            )}
            {card.card_type === "scout_card" && (
              <ScoutCard card={card} />
            )}
            {card.card_type === "draft_post_card" && (
              <DraftPostCard card={card} />
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
