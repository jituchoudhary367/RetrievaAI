"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, useScroll, useMotionValueEvent } from 'framer-motion';
import { Hexagon } from 'lucide-react';

const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    {...props}
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.2c3-.3 6-1.5 6-6.5a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 5 3 6.2 6 6.5a4.8 4.8 0 0 0-1 3.2v4" />
  </svg>
);
import { Button } from '@/components/ui/button';

export function Navbar() {
  const { scrollY } = useScroll();
  const [isScrolled, setIsScrolled] = useState(false);

  useMotionValueEvent(scrollY, "change", (latest) => {
    if (latest > 50) {
      setIsScrolled(true);
    } else {
      setIsScrolled(false);
    }
  });

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled 
          ? 'bg-[#05070B]/80 backdrop-blur-md border-b border-[rgba(255,255,255,0.06)] py-3 shadow-[0_4px_30px_rgba(0,0,0,0.1)]' 
          : 'bg-transparent border-transparent py-5'
      }`}
    >
      <div className="container mx-auto px-6 max-w-7xl flex items-center justify-between">
        
        {/* Left: Logo and Brand */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="relative flex items-center justify-center w-8 h-8">
            <img src="/logo.png" alt="RetrievaAI Logo" className="w-8 h-8 object-contain drop-shadow-md" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-white tracking-wide leading-tight">RetrievaAI</span>
            <span className="text-[10px] text-[#94A3B8] tracking-widest uppercase font-medium">Enterprise RAG Platform</span>
          </div>
        </Link>

        {/* Center: Navigation Links */}
        <div className="hidden md:flex items-center space-x-8">
          {['Product', 'Features', 'Solutions', 'Developers'].map((item) => (
            <Link 
              key={item} 
              href={`#${item.toLowerCase()}`}
              className="text-sm font-medium text-[#94A3B8] hover:text-white transition-colors"
            >
              {item}
            </Link>
          ))}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-4">
          <Link href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-[#94A3B8] hover:text-white transition-colors">
            <GithubIcon className="w-5 h-5" />
          </Link>
          <div className="hidden sm:block w-[1px] h-4 bg-[rgba(255,255,255,0.06)] mx-2" />
          <Link href="/login" className="hidden sm:block text-sm font-medium text-[#94A3B8] hover:text-white transition-colors">
            Log In
          </Link>
          <Link href="/signup">
            <Button className="bg-[#10B981] hover:bg-[#34D399] text-[#05070B] font-semibold text-sm px-5 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] transition-all">
              Get Started
            </Button>
          </Link>
        </div>

      </div>
    </motion.nav>
  );
}
