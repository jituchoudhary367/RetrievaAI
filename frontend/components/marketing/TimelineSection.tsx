"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, ScanText, Wrench, Scissors, Network, Database, Search, MessageSquare, ArrowRight } from 'lucide-react';

const steps = [
  { id: 1, title: 'Upload', desc: 'Securely ingest your files.', icon: UploadCloud },
  { id: 2, title: 'Extract OCR', desc: 'Extract text from any format.', icon: ScanText },
  { id: 3, title: 'Preprocess', desc: 'Clean and format data.', icon: Wrench },
  { id: 4, title: 'Chunk', desc: 'Split into semantic pieces.', icon: Scissors },
  { id: 5, title: 'Embed', desc: 'Convert text to vectors.', icon: Network },
  { id: 6, title: 'Index', desc: 'Store in vector database.', icon: Database },
  { id: 7, title: 'Retrieve', desc: 'Find relevant context.', icon: Search },
  { id: 8, title: 'Generate', desc: 'Produce accurate answers.', icon: MessageSquare }
];

export function TimelineSection() {
  return (
    <section className="py-24 bg-[#05070B] overflow-hidden border-t border-[rgba(255,255,255,0.02)] relative">
      
      {/* Background elements */}
      <div className="absolute inset-0 bg-transparent" style={{ opacity: 0.02 }} />

      <div className="container mx-auto px-6 max-w-7xl relative z-10">
        <div className="text-center mb-20">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-6">
            How RetrievaAI Works
          </h2>
          <p className="text-[#94A3B8] max-w-2xl mx-auto text-lg">
            A production-ready pipeline designed to transform your enterprise data into actionable intelligence.
          </p>
        </div>

        <div className="relative">
          {/* Scrollable container for horizontal timeline on smaller screens */}
          <div className="flex overflow-x-auto pb-10 hide-scrollbar scroll-smooth snap-x">
            <div className="flex items-center space-x-4 min-w-max px-4">
              {steps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: "-50px" }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                    whileHover={{ y: -5, borderColor: "rgba(16,185,129,0.5)" }}
                    className="w-48 bg-[#10161E] border border-[rgba(255,255,255,0.06)] rounded-2xl p-6 flex flex-col items-center text-center transition-colors shadow-sm snap-center group"
                  >
                    <div className="w-12 h-12 rounded-xl bg-[#0A0F14] border border-[rgba(255,255,255,0.06)] flex items-center justify-center mb-4 text-[#10B981] group-hover:bg-[#10B981]/10 group-hover:scale-110 transition-all duration-300">
                      <step.icon className="w-6 h-6" />
                    </div>
                    <h4 className="text-white font-bold mb-2">{step.title}</h4>
                    <p className="text-xs text-[#94A3B8] leading-relaxed">{step.desc}</p>
                  </motion.div>

                  {index < steps.length - 1 && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true, margin: "-50px" }}
                      transition={{ duration: 0.3, delay: (index * 0.1) + 0.1 }}
                      className="text-[rgba(255,255,255,0.2)]"
                    >
                      <ArrowRight className="w-6 h-6" />
                    </motion.div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      <style dangerouslySetInnerHTML={{__html: `
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}} />
    </section>
  );
}
