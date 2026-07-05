"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Terminal } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-16 md:pt-48 md:pb-24 overflow-hidden bg-[#05070B] border-b border-[rgba(255,255,255,0.04)]">
      
      {/* 1px Structural Grid Lines (Background) */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute left-[10%] top-0 bottom-0 w-[1px] bg-[rgba(255,255,255,0.02)]" />
        <div className="absolute left-[50%] top-0 bottom-0 w-[1px] bg-[rgba(255,255,255,0.02)] hidden lg:block" />
        <div className="absolute left-[90%] top-0 bottom-0 w-[1px] bg-[rgba(255,255,255,0.02)]" />
        <div className="absolute top-[30%] left-0 right-0 h-[1px] bg-[rgba(255,255,255,0.02)]" />
      </div>

      <div className="container mx-auto px-6 max-w-7xl relative z-10">
        <div className="flex flex-col lg:flex-row items-stretch gap-12 lg:gap-0">
          
          {/* LEFT COLUMN: Editorial Typography */}
          <div className="flex-1 flex flex-col justify-center lg:pr-12 pt-8 lg:pt-0">
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="flex items-center space-x-3 mb-8"
            >
              <div className="h-[1px] w-8 bg-[#10B981]" />
              <span className="text-[10px] font-mono tracking-widest uppercase text-[#10B981]">
                Enterprise Retrieval Augmented Generation
              </span>
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
              className="text-5xl sm:text-7xl lg:text-[85px] font-medium tracking-tighter mb-8 leading-[0.95] text-white"
            >
              Intelligence,<br/>
              <span className="text-[#94A3B8]">Architected.</span>
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 0.3, ease: "easeOut" }}
              className="max-w-md text-[#94A3B8] text-sm sm:text-base mb-12 font-normal leading-relaxed"
            >
              Deploy secure, high-performance semantic search and source-grounded LLM generation infrastructure directly onto your proprietary enterprise data.
            </motion.p>
            
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col sm:flex-row items-center gap-6"
            >
              <Link href="/signup">
                <Button className="h-12 px-8 rounded-none bg-white text-[#05070B] hover:bg-[#E2E8F0] text-sm font-semibold transition-all hover:-translate-y-[1px]">
                  Deploy Infrastructure
                </Button>
              </Link>
              <Link href="/docs" className="text-xs font-mono text-[#94A3B8] hover:text-white transition-colors flex items-center group">
                Read Documentation 
                <ArrowRight className="w-3 h-3 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
            </motion.div>
          </div>
          
          {/* RIGHT COLUMN: Asymmetrical interface slice */}
          <div className="flex-1 relative w-full h-[500px] lg:h-[650px] overflow-hidden lg:-mr-32 border-l border-t border-[rgba(255,255,255,0.06)] bg-[#0A0F14] lg:rounded-tl-2xl">
            
            <motion.div 
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
              className="absolute inset-0 p-8 flex flex-col"
            >
              {/* Fake IDE / Technical UI */}
              <div className="flex items-center justify-between mb-8">
                <div className="text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider">
                  pipeline.rs
                </div>
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-[rgba(255,255,255,0.2)]" />
                  <div className="w-1.5 h-1.5 rounded-full bg-[rgba(255,255,255,0.2)]" />
                </div>
              </div>

              <div className="flex-1 border border-[rgba(255,255,255,0.04)] bg-[#05070B] p-6 font-mono text-[11px] leading-loose text-[#94A3B8] overflow-hidden relative">
                <div className="absolute top-0 left-0 bottom-0 w-8 bg-[#0A0F14] border-r border-[rgba(255,255,255,0.04)] flex flex-col items-center py-6 space-y-3 text-[9px] opacity-40">
                  {Array.from({length: 20}).map((_, i) => <span key={i}>{i+1}</span>)}
                </div>
                
                <div className="pl-6 whitespace-pre">
                  <span className="text-[#10B981]">pub struct</span> <span className="text-white">RetrievalPipeline</span> {'{\n'}
                  {'    '}pub store: VectorStore,
                  {'\n    '}pub embedder: EmbeddingModel,
                  {'\n    '}pub llm: LanguageModel,
                  {'\n}\n\n'}
                  <span className="text-[#10B981]">impl</span> <span className="text-white">RetrievalPipeline</span> {'{\n'}
                  {'    '}<span className="text-[#10B981]">pub async fn</span> <span className="text-white">query</span>(&self, req: Query) -{'>'} Result {'{\n'}
                  {'        '}let ctx = self.store.<span className="text-white">search</span>(req.text).<span className="text-[#10B981]">await</span>?;
                  {'\n        '}let res = self.llm.<span className="text-white">generate</span>(ctx).<span className="text-[#10B981]">await</span>?;
                  {'\n        '}Ok(res)
                  {'\n    }\n'}
                  {'}'}
                </div>

                {/* Overlapping status panel */}
                <div className="absolute bottom-6 right-6 border border-[#10B981]/20 bg-[#05070B] p-4 flex flex-col gap-2 backdrop-blur-md">
                  <div className="flex items-center space-x-2 text-[10px] uppercase tracking-wider text-[#10B981]">
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#10B981]"></span>
                    </span>
                    System Operational
                  </div>
                  <div className="text-white font-mono text-xs">Latency: 42ms</div>
                  <div className="text-[#94A3B8] font-mono text-[10px]">p99 &lt; 100ms</div>
                </div>

              </div>
            </motion.div>
          </div>
          
        </div>
      </div>
    </section>
  );
}
