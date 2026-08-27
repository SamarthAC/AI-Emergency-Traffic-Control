import type { ReactNode } from "react";
import { motion } from "framer-motion";

interface CardProps {
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  accent?: "primary" | "emergency" | "neutral";
  className?: string;
  pulse?: boolean;
}

const accentClasses: Record<NonNullable<CardProps["accent"]>, string> = {
  primary: "border-primary/30",
  emergency: "border-emergency/50 shadow-glow-red",
  neutral: "border-border",
};

/** Standard dashboard card: title row + icon + animated entrance. */
export default function Card({ title, icon, children, accent = "neutral", className = "", pulse = false }: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`card-panel p-4 ${accentClasses[accent]} ${pulse ? "animate-pulse-slow" : ""} ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">{title}</h3>
        {icon && <span className="text-primary/80 text-base">{icon}</span>}
      </div>
      {children}
    </motion.div>
  );
}
