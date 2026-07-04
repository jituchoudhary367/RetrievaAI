"use client";

import React from 'react';
import { motion } from 'framer-motion';

const technologies = [
  "OpenAI", "Anthropic", "Gemini", "Llama", 
  "FastAPI", "Qdrant", "Redis", "Docker", 
  "Kubernetes", "LangChain"
];

export function TrustedTechSection() {
  return (
    <section className="py-20 bg-[#05070B] border-t border-[rgba(255,255,255,0.02)]">
      <div className="container mx-auto px-6 max-w-6xl">
        <p className="text-center text-[#94A3B8] text-sm font-semibold tracking-widest uppercase mb-10">
          Powered by Industry Leading Technologies
        </p>
        
        <div className="flex flex-wrap justify-center gap-4 md:gap-6">
          {technologies.map((tech, index) => (
            <motion.div
              key={tech}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              whileHover={{ scale: 1.05, backgroundColor: "#10161E", borderColor: "rgba(16,185,129,0.3)" }}
              className="flex items-center justify-center px-6 py-3 rounded-full bg-[#0A0F14] border border-[rgba(255,255,255,0.06)] transition-all cursor-default"
            >
              <span className="text-white/70 font-semibold text-sm tracking-wide">{tech}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
