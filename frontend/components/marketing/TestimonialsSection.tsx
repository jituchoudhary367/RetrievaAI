"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Quote } from 'lucide-react';

const testimonials = [
  {
    id: 1,
    quote: "RetrievaAI completely transformed how our engineering team interacts with our internal documentation. The semantic search is incredibly accurate.",
    name: "Alex Rivera",
    role: "Lead Engineer",
    company: "TechFlow Inc."
  },
  {
    id: 2,
    quote: "We evaluated several RAG platforms, and RetrievaAI's enterprise security features and decoupled architecture made it the clear winner.",
    name: "Sarah Chen",
    role: "CTO",
    company: "DataSphere"
  },
  {
    id: 3,
    quote: "The ability to stream responses while generating accurate inline citations has saved our legal team hundreds of hours in contract review.",
    name: "Marcus Johnson",
    role: "VP of Operations",
    company: "Nexus Legal"
  }
];

export function TestimonialsSection() {
  const [currentIndex, setCurrentIndex] = useState(0);

  const next = () => setCurrentIndex((prev) => (prev + 1) % testimonials.length);
  const prev = () => setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);

  useEffect(() => {
    const timer = setInterval(next, 6000);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="py-24 bg-[#0A0F14] border-t border-[rgba(255,255,255,0.02)] overflow-hidden">
      <div className="container mx-auto px-6 max-w-4xl relative">
        
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-white">
            Loved by Developers and Teams
          </h2>
        </div>

        <div className="relative h-[300px] sm:h-[250px] w-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentIndex}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
              className="absolute inset-0 flex flex-col items-center justify-center text-center px-4"
            >
              <Quote className="w-10 h-10 text-[#10B981]/20 mb-6" />
              <p className="text-xl sm:text-2xl font-medium text-white mb-8 leading-relaxed max-w-3xl">
                "{testimonials[currentIndex].quote}"
              </p>
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 rounded-full overflow-hidden border border-[#10B981]/30 bg-[#10161E]">
                  <img src={`https://api.dicebear.com/7.x/notionists/svg?seed=${testimonials[currentIndex].name}`} alt={testimonials[currentIndex].name} className="w-full h-full object-cover" />
                </div>
                <div className="text-left">
                  <div className="text-sm font-bold text-white">{testimonials[currentIndex].name}</div>
                  <div className="text-xs text-[#94A3B8]">{testimonials[currentIndex].role}, {testimonials[currentIndex].company}</div>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          <button 
            onClick={prev}
            className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 md:-translate-x-12 w-10 h-10 rounded-full border border-[rgba(255,255,255,0.1)] flex items-center justify-center text-[#94A3B8] hover:text-white hover:bg-[#10161E] transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button 
            onClick={next}
            className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 md:translate-x-12 w-10 h-10 rounded-full border border-[rgba(255,255,255,0.1)] flex items-center justify-center text-[#94A3B8] hover:text-white hover:bg-[#10161E] transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

      </div>
    </section>
  );
}
