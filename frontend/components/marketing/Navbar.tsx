"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { motion, useScroll, useMotionValueEvent } from 'framer-motion';
import { Button } from '@/components/ui/button';

export function Navbar() {
  const { scrollY } = useScroll();
  const [isScrolled, setIsScrolled] = useState(false);

  useMotionValueEvent(scrollY, "change", (latest) => {
    setIsScrolled(latest > 20);
  });

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-500 ${
        isScrolled 
          ? 'bg-[#05070B]/90 backdrop-blur-xl border-b border-[rgba(255,255,255,0.06)]' 
          : 'bg-transparent border-transparent'
      }`}
    >
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="flex items-center justify-between h-14">
          
          {/* Left: Logo and Brand */}
          <Link href="/" className="flex items-center space-x-2 group">
            <div className="w-5 h-5 relative flex items-center justify-center opacity-90 group-hover:opacity-100 transition-opacity">
              <img src="/logo.png" alt="RetrievaAI Logo" className="w-5 h-5 object-contain" />
            </div>
            <span className="font-semibold text-white tracking-tight text-sm">RetrievaAI</span>
          </Link>

          {/* Center: Navigation Links */}
          <div className="hidden md:flex items-center space-x-8">
            {['Platform', 'Infrastructure', 'Developers', 'Enterprise'].map((item) => (
              <Link 
                key={item} 
                href={`#${item.toLowerCase()}`}
                className="text-xs font-medium text-[#94A3B8] hover:text-white transition-colors"
              >
                {item}
              </Link>
            ))}
          </div>

          {/* Right: Actions */}
          <div className="flex items-center space-x-4">
            <Link href="/login" className="hidden sm:block text-xs font-medium text-[#94A3B8] hover:text-white transition-colors">
              Log In
            </Link>
            <div className="hidden sm:block w-[1px] h-3 bg-[rgba(255,255,255,0.1)]" />
            <Link href="/signup">
              <Button className="h-8 rounded-sm bg-white text-[#05070B] hover:bg-[#E2E8F0] text-xs font-semibold px-4 transition-all hover:-translate-y-[1px]">
                Deploy Now
              </Button>
            </Link>
          </div>

        </div>
      </div>
    </motion.nav>
  );
}
