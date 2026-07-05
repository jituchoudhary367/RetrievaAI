"use client";

import React from 'react';
import { motion } from 'framer-motion';

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-[#05070B] border-b border-[rgba(255,255,255,0.04)]">
      <div className="container mx-auto px-6 max-w-7xl">
        
        <div className="mb-20">
          <h2 className="text-3xl lg:text-4xl font-medium tracking-tight text-white mb-6 max-w-2xl">
            A strictly structural approach to enterprise search.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-px bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.04)]">
          
          {/* Feature 1: Large Editorial Block */}
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="md:col-span-12 lg:col-span-8 bg-[#05070B] p-12 lg:p-16"
          >
            <div className="text-[10px] font-mono tracking-widest uppercase text-[#94A3B8] mb-8">
              01 — Contextual AI
            </div>
            <h3 className="text-2xl lg:text-3xl font-medium text-white mb-4">
              Semantic Hybrid Search
            </h3>
            <p className="text-[#94A3B8] max-w-lg leading-relaxed font-normal">
              Combine sparse keyword matching with dense vector semantics. Our architecture ensures that high-precision domain terminology and broad conceptual queries are resolved simultaneously.
            </p>
          </motion.div>

          {/* Feature 2: Split Metric */}
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="md:col-span-6 lg:col-span-4 bg-[#0A0F14] p-12 lg:p-16 flex flex-col justify-between"
          >
            <div className="text-[10px] font-mono tracking-widest uppercase text-[#94A3B8] mb-8">
              02 — Velocity
            </div>
            <div>
              <div className="text-5xl font-medium text-white mb-2">&lt;50ms</div>
              <p className="text-[#94A3B8] text-sm">p99 retrieval latency</p>
            </div>
          </motion.div>

          {/* Feature 3: Split Block */}
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="md:col-span-6 lg:col-span-5 bg-[#05070B] p-12 lg:p-16"
          >
            <div className="text-[10px] font-mono tracking-widest uppercase text-[#94A3B8] mb-8">
              03 — Ingestion
            </div>
            <h3 className="text-xl font-medium text-white mb-4">
              Universal Document Parsing
            </h3>
            <p className="text-[#94A3B8] text-sm leading-relaxed">
              Native support for PDFs, DOCX, HTML, and images. Our pipeline handles OCR, semantic chunking, and metadata extraction without external dependencies.
            </p>
          </motion.div>

          {/* Feature 4: Code Block */}
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="md:col-span-12 lg:col-span-7 bg-[#0A0F14] p-12 lg:p-16 relative overflow-hidden"
          >
            <div className="text-[10px] font-mono tracking-widest uppercase text-[#94A3B8] mb-8">
              04 — Extensibility
            </div>
            <h3 className="text-xl font-medium text-white mb-6">
              Modular Architecture
            </h3>
            <div className="bg-[#05070B] border border-[rgba(255,255,255,0.06)] p-6 font-mono text-xs text-[#94A3B8]">
              <span className="text-[#10B981]">import</span> {'{'} Pipeline {'}'} <span className="text-[#10B981]">from</span> '@retrieva/sdk';<br/><br/>
              <span className="text-[#10B981]">const</span> rag = <span className="text-[#10B981]">new</span> Pipeline({'{\n'}
              {'  '}llm: <span className="text-white">'claude-3-sonnet'</span>,{'\n'}
              {'  '}embedder: <span className="text-white">'bge-large-en-v1.5'</span>,{'\n'}
              {'  '}store: <span className="text-white">'qdrant'</span>{'\n'}
              {'}'});
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
