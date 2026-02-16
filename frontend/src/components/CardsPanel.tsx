import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart2,
  Minus,
  Plus,
  Activity,
  Database,
  Compass,
  FileText,
  Rocket,
  GitCompareArrows,
  RefreshCw,
} from "lucide-react";
import WandBHealthCard from "./WandBHealthCard";
import DataCard from "./DataCard";
import ScoutCard from "./ScoutCard";
import DraftPostCard from "./DraftPostCard";
import LaunchCard from "./LaunchCard";
import ComparisonCard from "./ComparisonCard";
import ConversionCard from "./ConversionCard";
import type { CardData } from "../types";

interface Props {
  cards: CardData[];
  onWandbUrl?: (url: string) => void;
}

const CARD_META: Record<string, { label: string; icon: React.ReactNode }> = {
  wandb_health: { label: "Health Card", icon: <Activity size={12} /> },
  data_card: { label: "Data Card", icon: <Database size={12} /> },
  scout_card: { label: "Scout", icon: <Compass size={12} /> },
  draft_post_card: { label: "Draft", icon: <FileText size={12} /> },
  launch_card: { label: "Launch", icon: <Rocket size={12} /> },
  comparison_card: { label: "Comparison", icon: <GitCompareArrows size={12} /> },
  conversion_card: { label: "Conversion", icon: <RefreshCw size={12} /> },
};

function CollapsibleCard({
  card,
  collapsed,
  onToggle,
  children,
}: {
  card: CardData;
  collapsed: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  const meta = CARD_META[card.card_type] || { label: "Card", icon: null };

  if (collapsed) {
    return (
      <button
        onClick={onToggle}
        className="w-full bg-white rounded-xl border border-stone-200 shadow-sm hover:shadow-md transition-all duration-200 px-4 py-3 flex items-center gap-3 text-left group"
      >
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-stone-100 text-stone-500 border border-stone-200 flex-shrink-0">
          {meta.icon}
          {meta.label}
        </div>
        <span className="text-sm text-stone-700 font-serif truncate flex-1">
          {card.title}
        </span>
        <Plus
          size={14}
          className="text-stone-400 group-hover:text-nobel-gold transition-colors flex-shrink-0"
        />
      </button>
    );
  }

  return (
    <div className="relative group/card">
      {children}
      <button
        onClick={onToggle}
        className="absolute top-2.5 left-1/2 -translate-x-1/2 z-10 p-0.5 rounded text-stone-500"
        title="Collapse"
      >
        <Minus size={14} />
      </button>
    </div>
  );
}

export default function CardsPanel({ cards, onWandbUrl }: Props) {
  const [collapsedSet, setCollapsedSet] = useState<Set<number>>(new Set());

  const toggle = (index: number) => {
    setCollapsedSet((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

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
            <CollapsibleCard
              card={card}
              collapsed={collapsedSet.has(i)}
              onToggle={() => toggle(i)}
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
              {card.card_type === "launch_card" && (
                <LaunchCard card={card} onWandbUrl={onWandbUrl} />
              )}
              {card.card_type === "comparison_card" && (
                <ComparisonCard card={card} />
              )}
              {card.card_type === "conversion_card" && (
                <ConversionCard card={card} />
              )}
            </CollapsibleCard>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
