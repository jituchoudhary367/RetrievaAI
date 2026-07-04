"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Hexagon } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CtaSection() {
  return (
    <section className="py-24 bg-[#05070B] relative overflow-hidden">
      
      {/* Background details */}
      <div className="absolute inset-0 bg-[#10161E] [clip-path:polygon(0_0,100%_10vw,100%_100%,0_100%)] sm:[clip-path:polygon(0_0,100%_5vw,100%_100%,0_100%)] pointer-events-none" />
      <div className="absolute top-[50%] left-[80%] translate-x-[-50%] translate-y-[-50%] w-[600px] h-[300px] bg-[#10B981]/10 rounded-full blur-[100px] pointer-events-none mix-blend-screen" />

      <div className="container mx-auto px-6 max-w-7xl relative z-10">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="flex flex-col lg:flex-row items-center justify-between gap-10 bg-[#0A0F14] border border-[#10B981]/20 rounded-[2.5rem] p-10 md:p-16 shadow-[0_0_50px_rgba(16,185,129,0.05)]"
        >
          {/* Left Content */}
          <div className="flex-1 max-w-2xl text-center lg:text-left">
            <div className="flex items-center justify-center lg:justify-start space-x-3 mb-6">
              <div className="relative flex items-center justify-center w-10 h-10">
                <Hexagon className="w-10 h-10 text-[#10B981] absolute fill-[#10B981]/20" />
                <div className="w-3 h-3 bg-[#10B981] rounded-full relative z-10 shadow-[0_0_15px_#10B981]" />
              </div>
            </div>
            
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-6">
              Ready to build with your knowledge?
            </h2>
            <p className="text-[#94A3B8] text-lg font-medium">
              Join teams building the next generation of AI applications using RetrievaAI.
            </p>
          </div>

          {/* Right Action */}
          <div className="flex-shrink-0">
            <Link href="/signup">
              <Button size="lg" className="h-16 px-12 text-lg rounded-full bg-[#10B981] hover:bg-[#34D399] text-[#05070B] shadow-[0_0_30px_rgba(16,185,129,0.4)] hover:shadow-[0_0_50px_rgba(16,185,129,0.6)] hover:-translate-y-1 transition-all font-bold">
                Get Started Free
              </Button>
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
