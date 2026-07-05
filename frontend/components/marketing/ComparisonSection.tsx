"use client";

import React from 'react';
import { motion } from 'framer-motion';

export function ComparisonSection() {
  return (
    <section className="py-24 bg-[#0A0F14] relative border-b border-[rgba(255,255,255,0.04)]">
      <div className="container mx-auto px-6 max-w-4xl relative z-10">
        
        <div className="mb-20 text-center">
          <h2 className="text-3xl font-medium tracking-tight text-white">
            The Evolution of Enterprise AI
          </h2>
        </div>

        <div className="flex flex-col items-center relative">
          
          {/* Vertical 1px line */}
          <div className="absolute top-0 bottom-0 left-[50%] w-[1px] bg-[rgba(255,255,255,0.06)] -translate-x-1/2" />

          {/* Traditional AI Block */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            className="w-full max-w-md bg-[#05070B] border border-[rgba(255,255,255,0.06)] p-8 relative z-10 mb-16 opacity-50 grayscale"
          >
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#94A3B8] mb-6">
              Legacy Approach
            </div>
            <h3 className="text-xl font-medium text-white mb-6 line-through decoration-[rgba(255,255,255,0.2)]">
              Traditional LLMs
            </h3>
            <ul className="space-y-4 font-mono text-xs text-[#94A3B8]">
              <li className="flex items-start">
                <span className="mr-3 opacity-50">[x]</span> Hallucinations
              </li>
              <li className="flex items-start">
                <span className="mr-3 opacity-50">[x]</span> Generic public knowledge
              </li>
              <li className="flex items-start">
                <span className="mr-3 opacity-50">[x]</span> No exact citations
              </li>
            </ul>
          </motion.div>

          {/* Arrow Indicator */}
          <div className="w-10 h-10 bg-[#0A0F14] border border-[rgba(255,255,255,0.06)] rounded-full flex items-center justify-center relative z-10 mb-16 text-[#94A3B8]">
            ↓
          </div>

          {/* RetrievaAI Block */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            className="w-full max-w-md bg-[#05070B] border-t-2 border-[#10B981] border-l border-r border-b border-[rgba(255,255,255,0.06)] p-8 relative z-10 shadow-[0_20px_40px_rgba(16,185,129,0.05)]"
          >
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#10B981] mb-6">
              Modern Architecture
            </div>
            <h3 className="text-xl font-medium text-white mb-6">
              RetrievaAI RAG
            </h3>
            <ul className="space-y-4 font-mono text-xs text-white">
              <li className="flex items-start">
                <span className="mr-3 text-[#10B981]">[✓]</span> Source-grounded accuracy
              </li>
              <li className="flex items-start">
                <span className="mr-3 text-[#10B981]">[✓]</span> Isolated proprietary data
              </li>
              <li className="flex items-start">
                <span className="mr-3 text-[#10B981]">[✓]</span> Line-level citations
              </li>
              <li className="flex items-start">
                <span className="mr-3 text-[#10B981]">[✓]</span> Enterprise RBAC security
              </li>
            </ul>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
