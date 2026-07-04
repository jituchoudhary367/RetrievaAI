"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Frown, Smile, XCircle, CheckCircle2 } from 'lucide-react';

export function ComparisonSection() {
  return (
    <section className="py-24 bg-[#0A0F14] relative overflow-hidden border-t border-[rgba(255,255,255,0.02)]">
      <div className="container mx-auto px-6 max-w-6xl relative z-10">
        
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-6">
            Why Choose RetrievaAI
          </h2>
        </div>

        <div className="grid md:grid-cols-2 gap-8 lg:gap-12">
          
          {/* Traditional AI */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="bg-[#10161E] border border-[rgba(255,255,255,0.06)] rounded-3xl p-8 lg:p-10 relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#EF4444]/5 rounded-full blur-[80px] pointer-events-none group-hover:bg-[#EF4444]/10 transition-colors" />
            
            <div className="flex items-center space-x-4 mb-8">
              <div className="w-12 h-12 rounded-2xl bg-[#EF4444]/10 border border-[#EF4444]/20 flex items-center justify-center text-[#EF4444]">
                <Frown className="w-6 h-6" />
              </div>
              <h3 className="text-2xl font-bold text-white">Traditional AI Solutions</h3>
            </div>
            
            <ul className="space-y-5">
              {['Hallucinations', 'No proprietary knowledge', 'No citations', 'Limited security', 'Generic responses'].map((item) => (
                <li key={item} className="flex items-start text-[#94A3B8] font-medium text-lg">
                  <XCircle className="w-6 h-6 mr-4 text-[#EF4444] shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </motion.div>

          {/* RetrievaAI */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-[#10161E] border border-[#10B981]/30 rounded-3xl p-8 lg:p-10 relative overflow-hidden group shadow-[0_0_40px_rgba(16,185,129,0.05)] hover:shadow-[0_0_60px_rgba(16,185,129,0.1)] transition-shadow"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#10B981]/10 rounded-full blur-[80px] pointer-events-none group-hover:bg-[#10B981]/20 transition-colors" />
            
            <div className="flex items-center space-x-4 mb-8 relative z-10">
              <div className="w-12 h-12 rounded-2xl bg-[#10B981]/20 border border-[#10B981]/40 flex items-center justify-center text-[#10B981]">
                <Smile className="w-6 h-6" />
              </div>
              <h3 className="text-2xl font-bold text-white">RetrievaAI</h3>
            </div>
            
            <ul className="space-y-5 relative z-10">
              {['Source-grounded answers', 'Built on your documents', 'Hybrid Search', 'Enterprise Security', 'Exact citations', 'Context-aware responses'].map((item) => (
                <li key={item} className="flex items-start text-white font-medium text-lg">
                  <CheckCircle2 className="w-6 h-6 mr-4 text-[#10B981] shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
