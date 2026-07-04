"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { CheckCircle2, FileText, Code, Image as ImageIcon, File, Globe, Terminal } from 'lucide-react';
import { Button } from '@/components/ui/button';

const FloatingIcon = ({ children, delay, className }: { children: React.ReactNode, delay: number, className: string }) => (
  <motion.div
    initial={{ y: 0 }}
    animate={{ y: [-10, 10, -10] }}
    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay }}
    className={`absolute flex items-center justify-center w-12 h-12 rounded-xl bg-[#10161E] border border-[rgba(255,255,255,0.06)] shadow-xl ${className}`}
  >
    {children}
  </motion.div>
);

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden bg-[#05070B]">
      
      {/* Background Glows */}
      <div className="absolute top-[20%] left-[-10%] w-[500px] h-[500px] bg-[#10B981]/10 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />
      <div className="absolute top-[10%] right-[-5%] w-[600px] h-[600px] bg-[#10B981]/5 rounded-full blur-[150px] pointer-events-none mix-blend-screen" />
      
      <div className="container mx-auto px-6 max-w-7xl relative z-10">
        <div className="flex flex-col lg:flex-row items-center gap-16 lg:gap-8">
          
          {/* LEFT COLUMN */}
          <div className="flex-1 flex flex-col items-center lg:items-start text-center lg:text-left">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center rounded-full border border-[rgba(255,255,255,0.06)] bg-[#10161E] px-4 py-1.5 text-xs font-semibold text-[#94A3B8] mb-8"
            >
              <span className="text-[#10B981] mr-2 flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10B981]"></span>
              </span>
              AI-Powered. Secure. Scalable.
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl mb-6 leading-[1.1] text-white"
            >
              Enterprise RAG Platform <br/>
              for <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#10B981] to-[#34D399]">Your Knowledge</span>
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="max-w-2xl text-[#94A3B8] text-lg sm:text-xl mb-10 font-medium leading-relaxed"
            >
              Build accurate AI assistants that understand your documents, applications, and enterprise knowledge using hybrid retrieval, OCR, semantic search, reranking, and source-grounded generation.
            </motion.p>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center gap-6 mb-12"
            >
              <Link href="/signup">
                <Button size="lg" className="h-14 px-10 text-base rounded-full bg-[#10B981] hover:bg-[#34D399] text-[#05070B] shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] transition-all font-semibold">
                  Start Building
                </Button>
              </Link>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="flex flex-wrap items-center justify-center lg:justify-start gap-6 text-sm font-medium text-[#94A3B8]"
            >
              {['SOC2 Ready', 'Self Hosted', 'Enterprise Security'].map((item) => (
                <div key={item} className="flex items-center">
                  <CheckCircle2 className="w-4 h-4 mr-2 text-[#10B981]" />
                  {item}
                </div>
              ))}
            </motion.div>
          </div>
          
          {/* RIGHT COLUMN */}
          <div className="flex-1 relative w-full max-w-2xl lg:max-w-none">
            
            {/* Connecting Lines (Simulated via SVG) */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20 hidden lg:block" style={{ zIndex: 0 }}>
              <path d="M 0 200 C 100 200, 200 100, 300 250" fill="none" stroke="#10B981" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
              <path d="M 50 100 C 150 100, 150 300, 250 250" fill="none" stroke="#10B981" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_15s_linear_infinite]" />
              <path d="M 100 350 C 200 350, 150 200, 250 250" fill="none" stroke="#10B981" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_25s_linear_infinite]" />
            </svg>

            <style dangerouslySetInnerHTML={{__html: `
              @keyframes dash {
                to { stroke-dashoffset: -1000; }
              }
            `}} />

            {/* Floating File Icons */}
            <FloatingIcon delay={0} className="top-10 left-10 text-red-400 bg-red-400/5 border-red-400/20 z-20 hidden lg:flex">
              <FileText className="w-6 h-6" />
            </FloatingIcon>
            <FloatingIcon delay={1} className="bottom-20 left-0 text-blue-400 bg-blue-400/5 border-blue-400/20 z-20 hidden lg:flex">
              <File className="w-6 h-6" />
            </FloatingIcon>
            <FloatingIcon delay={0.5} className="top-32 right-[-20px] text-purple-400 bg-purple-400/5 border-purple-400/20 z-20 hidden lg:flex">
              <Code className="w-6 h-6" />
            </FloatingIcon>
            <FloatingIcon delay={1.5} className="bottom-10 right-10 text-emerald-400 bg-emerald-400/5 border-emerald-400/20 z-20 hidden lg:flex">
              <Globe className="w-6 h-6" />
            </FloatingIcon>
            <FloatingIcon delay={0.8} className="top-[-10px] right-20 text-orange-400 bg-orange-400/5 border-orange-400/20 z-20 hidden lg:flex">
              <ImageIcon className="w-6 h-6" />
            </FloatingIcon>
            
            {/* Dashboard Mockup */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, rotateY: -10 }}
              animate={{ opacity: 1, scale: 1, rotateY: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="relative z-10 w-full rounded-2xl border border-[rgba(255,255,255,0.06)] bg-[#0A0F14] shadow-2xl overflow-hidden aspect-[4/3] flex flex-col perspective-1000"
              style={{ transformStyle: 'preserve-3d', boxShadow: '0 25px 50px -12px rgba(16,185,129,0.1)' }}
            >
              {/* Dashboard Topbar */}
              <div className="h-10 border-b border-[rgba(255,255,255,0.06)] bg-[#10161E] flex items-center px-4 justify-between">
                <div className="flex space-x-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#ef4444]/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-[#22C55E]/80" />
                </div>
                <div className="h-4 w-48 bg-[#05070B] rounded-md border border-[rgba(255,255,255,0.06)]" />
                <div className="w-6 h-6 rounded-full bg-[#10B981]/20 border border-[#10B981]/50 flex items-center justify-center">
                  <span className="text-[8px] font-bold text-[#10B981]">U</span>
                </div>
              </div>
              
              {/* Dashboard Body */}
              <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <div className="w-16 md:w-48 border-r border-[rgba(255,255,255,0.06)] bg-[#0A0F14] p-3 flex flex-col gap-2 hidden sm:flex">
                   <div className="h-8 rounded bg-[#10B981]/10 border border-[#10B981]/30 flex items-center px-2">
                     <Terminal className="w-4 h-4 text-[#10B981] mr-2" />
                     <div className="h-2 w-16 bg-[#10B981]/50 rounded hidden md:block" />
                   </div>
                   <div className="h-6 rounded bg-[#10161E] mt-4 flex items-center px-2">
                     <div className="h-2 w-20 bg-white/10 rounded hidden md:block" />
                   </div>
                   <div className="h-6 rounded bg-[#10161E] flex items-center px-2">
                     <div className="h-2 w-16 bg-white/10 rounded hidden md:block" />
                   </div>
                   <div className="h-6 rounded bg-[#10161E] flex items-center px-2">
                     <div className="h-2 w-24 bg-white/10 rounded hidden md:block" />
                   </div>
                </div>
                
                {/* Main Content */}
                <div className="flex-1 p-4 md:p-6 flex flex-col gap-4 bg-[#05070B]">
                  {/* Top Stats */}
                  <div className="grid grid-cols-3 gap-3">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="bg-[#10161E] border border-[rgba(255,255,255,0.06)] rounded-lg p-3 flex flex-col justify-center">
                        <div className="h-2 w-12 bg-white/20 rounded mb-2" />
                        <div className="h-4 w-16 bg-white/80 rounded" />
                      </div>
                    ))}
                  </div>
                  
                  {/* Middle Charts & Chat */}
                  <div className="flex-1 flex gap-4 h-0">
                    <div className="flex-1 bg-[#10161E] border border-[rgba(255,255,255,0.06)] rounded-lg p-4 flex flex-col">
                      <div className="h-3 w-32 bg-white/20 rounded mb-4" />
                      {/* Fake Chart */}
                      <div className="flex-1 flex items-end gap-2 pb-2">
                        {[40, 70, 30, 90, 50, 80].map((h, i) => (
                          <div key={i} className="w-full bg-[#10B981]/20 rounded-t-sm relative group overflow-hidden" style={{ height: `${h}%` }}>
                            <div className="absolute bottom-0 w-full bg-[#10B981] transition-all duration-1000" style={{ height: '0%' }} ref={(el) => { if(el) setTimeout(()=> el.style.height='100%', 500) }} />
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="w-1/3 bg-[#10161E] border border-[rgba(255,255,255,0.06)] rounded-lg p-3 hidden md:flex flex-col gap-2 overflow-hidden">
                      <div className="h-3 w-20 bg-white/20 rounded mb-2" />
                      <div className="self-end bg-[#10B981]/20 border border-[#10B981]/30 p-2 rounded-lg rounded-tr-sm max-w-[80%]">
                        <div className="h-2 w-24 bg-white/80 rounded" />
                      </div>
                      <div className="self-start bg-[#0A0F14] border border-[rgba(255,255,255,0.06)] p-2 rounded-lg rounded-tl-sm max-w-[90%]">
                        <div className="h-2 w-32 bg-white/60 rounded mb-1" />
                        <div className="h-2 w-28 bg-white/60 rounded" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
          
        </div>
      </div>
    </section>
  );
}
