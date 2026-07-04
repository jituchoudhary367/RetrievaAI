"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Search, FileText, BarChart3, ShieldCheck, Blocks } from 'lucide-react';

const features = [
  {
    title: 'AI Chat',
    desc: 'Engage in natural, context-aware conversations backed by your exact document sources and inline citations.',
    icon: MessageSquare
  },
  {
    title: 'Hybrid Search',
    desc: 'Combine semantic vector search with keyword matching to retrieve the most relevant information with high precision.',
    icon: Search
  },
  {
    title: 'Document Ingestion',
    desc: 'Effortlessly upload and process PDFs, DOCX, TXT, and HTML files with automatic chunking and OCR capabilities.',
    icon: FileText
  },
  {
    title: 'Analytics',
    desc: 'Gain actionable insights into query performance, retrieval accuracy, and system health through visual dashboards.',
    icon: BarChart3
  },
  {
    title: 'Enterprise Security',
    desc: 'Keep your data safe with robust Role-Based Access Control, tenant isolation, and SOC2 compliant infrastructure.',
    icon: ShieldCheck
  },
  {
    title: 'Extensible Tools',
    desc: 'Easily swap out LLMs, embedding models, and vector stores with our decoupled, modular microservice architecture.',
    icon: Blocks
  }
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-[#0A0F14] border-t border-[rgba(255,255,255,0.02)]">
      <div className="container mx-auto px-6 max-w-7xl">
        
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-6">
            Powerful Features for Modern Teams
          </h2>
          <p className="text-[#94A3B8] max-w-2xl mx-auto text-lg">
            Built from the ground up for performance, scalability, and security.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -5, borderColor: "rgba(16,185,129,0.3)" }}
              className="bg-[#10161E] border border-[rgba(255,255,255,0.06)] rounded-2xl p-8 flex flex-col transition-all group"
            >
              <div className="w-12 h-12 rounded-xl bg-[#05070B] border border-[rgba(255,255,255,0.06)] flex items-center justify-center mb-6 text-[#10B981] group-hover:bg-[#10B981]/10 group-hover:border-[#10B981]/30 transition-colors">
                <feature.icon className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-[#94A3B8] leading-relaxed">
                {feature.desc}
              </p>
            </motion.div>
          ))}
        </div>
        
      </div>
    </section>
  );
}
