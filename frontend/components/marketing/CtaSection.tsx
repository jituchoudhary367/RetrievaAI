"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';

export function CtaSection() {
  return (
    <section className="py-32 bg-[#05070B] border-b border-[rgba(255,255,255,0.04)]">
      <div className="container mx-auto px-6 max-w-7xl">
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="flex flex-col items-center text-center max-w-3xl mx-auto"
        >
          <div className="w-[1px] h-12 bg-[#10B981] mb-8" />
          
          <h2 className="text-4xl md:text-6xl font-medium tracking-tight text-white mb-8 leading-[1.1]">
            Initialize your infrastructure today.
          </h2>
          
          <Link href="/signup">
            <Button className="h-12 px-8 rounded-none bg-white text-[#05070B] hover:bg-[#E2E8F0] text-sm font-semibold transition-all hover:-translate-y-[1px]">
              Deploy Now
            </Button>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
