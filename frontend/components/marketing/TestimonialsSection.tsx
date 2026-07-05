"use client";

import React from 'react';
import { motion } from 'framer-motion';

const cases = [
  {
    id: 1,
    metric: "400%",
    metricLabel: "Increase in retrieval accuracy",
    quote: "RetrievaAI completely transformed how our engineering team interacts with our internal documentation.",
    name: "Alex Rivera",
    role: "Lead Engineer",
    company: "TechFlow Inc."
  },
  {
    id: 2,
    metric: "120hrs",
    metricLabel: "Saved per week on contract review",
    quote: "The ability to stream responses while generating accurate inline citations has been invaluable.",
    name: "Marcus Johnson",
    role: "VP of Operations",
    company: "Nexus Legal"
  },
  {
    id: 3,
    metric: "SOC2",
    metricLabel: "Compliant deployment on day one",
    quote: "We evaluated several RAG platforms, and RetrievaAI's enterprise security features made it the clear winner.",
    name: "Sarah Chen",
    role: "CTO",
    company: "DataSphere"
  }
];

export function TestimonialsSection() {
  return (
    <section className="py-24 bg-[#05070B] border-b border-[rgba(255,255,255,0.04)]">
      <div className="container mx-auto px-6 max-w-7xl">
        
        <div className="mb-20">
          <h2 className="text-3xl font-medium tracking-tight text-white mb-6">
            Production Outcomes
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.04)]">
          {cases.map((item, index) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="bg-[#0A0F14] p-10 flex flex-col justify-between"
            >
              <div>
                <div className="text-4xl font-medium text-white mb-1">{item.metric}</div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-[#10B981] mb-8">
                  {item.metricLabel}
                </div>
                <p className="text-sm text-[#94A3B8] leading-relaxed mb-12">
                  "{item.quote}"
                </p>
              </div>
              
              <div className="flex items-center space-x-3 pt-6 border-t border-[rgba(255,255,255,0.06)]">
                <div className="w-8 h-8 rounded-full overflow-hidden bg-[#05070B] grayscale opacity-80">
                  <img src={`https://api.dicebear.com/7.x/notionists/svg?seed=${item.name}`} alt={item.name} className="w-full h-full object-cover" />
                </div>
                <div>
                  <div className="text-xs font-medium text-white">{item.name}</div>
                  <div className="text-[10px] text-[#94A3B8]">{item.role}, {item.company}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}
