"use client";

import React from 'react';
import { motion } from 'framer-motion';

const steps = [
  { id: 1, title: 'Upload', desc: 'Ingest raw sources.' },
  { id: 2, title: 'Parse', desc: 'OCR & text extraction.' },
  { id: 3, title: 'Chunk', desc: 'Semantic segmentation.' },
  { id: 4, title: 'Embed', desc: 'Vector generation.' },
  { id: 5, title: 'Index', desc: 'High-speed storage.' },
  { id: 6, title: 'Retrieve', desc: 'Hybrid retrieval.' },
  { id: 7, title: 'Generate', desc: 'Grounded response.' }
];

export function TimelineSection() {
  return (
    <section className="py-24 bg-[#05070B] overflow-hidden border-b border-[rgba(255,255,255,0.04)] relative">
      <div className="container mx-auto px-6 max-w-7xl relative z-10">
        
        <div className="mb-20">
          <h2 className="text-sm font-mono tracking-widest uppercase text-[#94A3B8] mb-4">
            [ Architecture ]
          </h2>
          <p className="text-3xl font-medium tracking-tight text-white max-w-xl">
            A linear production pipeline designed to transform raw unstructured data into actionable intelligence.
          </p>
        </div>

        <div className="relative pt-10 pb-10">
          
          {/* Thin horizontal line traversing the entire width */}
          <div className="absolute top-[68px] left-0 right-0 h-[1px] bg-[rgba(255,255,255,0.06)] hidden lg:block" />

          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8 lg:gap-4 relative z-10">
            {steps.map((step, index) => (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="flex flex-row lg:flex-col items-center lg:items-start group w-full lg:w-auto"
              >
                {/* Node */}
                <div className="relative w-12 h-12 lg:mb-6 shrink-0 flex items-center justify-center">
                  <div className="absolute inset-0 bg-[#05070B] group-hover:bg-[#10161E] border border-[rgba(255,255,255,0.1)] transition-colors" />
                  <span className="relative text-[10px] font-mono text-[#94A3B8] group-hover:text-white transition-colors">
                    0{step.id}
                  </span>
                  
                  {/* Vertical line connecting mobile layout */}
                  {index < steps.length - 1 && (
                    <div className="absolute top-12 bottom-[-2rem] left-1/2 w-[1px] bg-[rgba(255,255,255,0.06)] lg:hidden" />
                  )}
                </div>

                {/* Content */}
                <div className="ml-6 lg:ml-0 flex flex-col">
                  <div className="flex items-center space-x-2 mb-1">
                    {index === steps.length - 1 ? (
                      <div className="w-1.5 h-1.5 bg-[#10B981]" />
                    ) : (
                      <div className="w-1.5 h-1.5 bg-[rgba(255,255,255,0.2)]" />
                    )}
                    <h4 className="text-xs font-mono uppercase tracking-wider text-white">
                      {step.title}
                    </h4>
                  </div>
                  <p className="text-[11px] font-mono text-[#94A3B8]">
                    {step.desc}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}
