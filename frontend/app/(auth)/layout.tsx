"use client";

import React from 'react';
import { Hexagon, Search, MessageSquare, ShieldCheck, Activity, Globe, Sun, Moon } from 'lucide-react';
import Link from 'next/link';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[#0b0f19] text-white font-sans selection:bg-[#10b981] selection:text-white dark">
      {/* Left pane - Visual/Branding (Hidden on mobile) */}
      <div className="hidden md:flex md:w-[50%] lg:w-[45%] bg-[#06090e] p-12 lg:p-20 flex-col justify-start relative overflow-hidden border-r border-white/5">
        {/* Abstract glowing backgrounds */}
        <div className="absolute top-[20%] left-[-10%] w-[400px] h-[400px] bg-[#10b981]/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-[#0ea5e9]/10 rounded-full blur-[120px] pointer-events-none" />
        
        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-transparent" style={{ opacity: 0.05 }} />
        
        {/* Logo */}
        <Link href="/" className="relative z-10 flex items-center gap-3 w-fit group mb-12">
          <div className="flex items-center justify-center relative w-20 h-20">
            {/* Custom Logo */}
            <img src="/logo.ico" alt="RetrievaAI Logo" className="w-20 h-20 object-contain drop-shadow-md" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-xl tracking-wider text-white uppercase leading-none mb-1">RetrievaAI</span>
            <span className="text-[11px] text-[#10b981] font-semibold tracking-wide uppercase">Retrieve. Understand. Generate.</span>
          </div>
        </Link>

        {/* Hero Text */}
        <div className="relative z-10 max-w-lg mb-10">
          <div className="inline-flex items-center rounded-full border border-[#10b981]/30 bg-[#10b981]/10 px-3 py-1 text-[10px] font-bold text-[#10b981] mb-6 tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] mr-2"></span>
            AI-POWERED KNOWLEDGE PLATFORM
          </div>
          <h1 className="text-4xl lg:text-[2.75rem] font-bold text-white mb-6 leading-[1.2] tracking-tight">
            Unlock the Power of <br />
            Your <span className="text-[#10b981]">Knowledge</span>
          </h1>
          <p className="text-zinc-400 text-sm leading-relaxed max-w-[400px]">
            A production-ready Retrieval Augmented Generation platform to search, chat, and analyze your data with enterprise-grade AI.
          </p>
        </div>

        {/* Feature List */}
        <div className="relative z-10 flex flex-col gap-6 max-w-md">
          {[
            { icon: Search, title: "Intelligent Search", desc: "Hybrid search across vectors and keywords" },
            { icon: MessageSquare, title: "AI Chat Assistant", desc: "Context-aware conversations with citations" },
            { icon: ShieldCheck, title: "Secure & Scalable", desc: "Enterprise-grade security and performance" },
            { icon: Activity, title: "Real-time Analytics", desc: "Monitor usage, performance and quality" },
          ].map((feature, idx) => (
            <div key={idx} className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-[#0b0f19] border border-white/5 flex items-center justify-center shadow-lg">
                <feature.icon className="w-5 h-5 text-[#10b981]" />
              </div>
              <div className="flex flex-col">
                <h3 className="text-sm font-semibold text-white mb-0.5">{feature.title}</h3>
                <p className="text-xs text-zinc-500">{feature.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Abstract 3D Cube Illustration at Bottom */}
        <div className="absolute bottom-[-5%] right-[-5%] w-[400px] h-[400px] opacity-80 mix-blend-screen pointer-events-none">
          <div className="relative w-full h-full flex items-center justify-center">
            {/* Base rings */}
            <div className="absolute w-[250px] h-[100px] border-2 border-[#10b981]/20 rounded-[50%] mt-40 shadow-[0_0_30px_rgba(16,185,129,0.2)]"></div>
            <div className="absolute w-[300px] h-[120px] border border-[#0ea5e9]/10 rounded-[50%] mt-40"></div>
            <div className="absolute w-[350px] h-[140px] border border-[#10b981]/5 rounded-[50%] mt-40"></div>
            
            {/* Glowing Cube */}
            <div className="absolute mb-10">
              <div className="relative flex items-center justify-center drop-shadow-[0_0_50px_rgba(16,185,129,0.4)]">
                 <svg viewBox="0 0 100 115" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-32 h-32">
                  <path d="M50 0L93.3013 25V75L50 100L6.69873 75V25L50 0Z" stroke="#0ea5e9" strokeWidth="1" fill="#0ea5e9" fillOpacity="0.05"/>
                  <path d="M50 15L75.9808 30V60L50 75L24.0192 60V30L50 15Z" stroke="#10b981" strokeWidth="2" fill="#10b981" fillOpacity="0.1"/>
                  <path d="M50 35L62.9904 42.5V57.5L50 65L37.0096 57.5V42.5L50 35Z" fill="#10b981"/>
                  <path d="M50 15V35M24.0192 30L37.0096 42.5M75.9808 30L62.9904 42.5M75.9808 60L62.9904 57.5M24.0192 60L37.0096 57.5M50 75V65" stroke="#10b981" strokeWidth="2" strokeOpacity="0.5"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right pane - Auth Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 md:p-12 relative bg-[#0b0f19] overflow-hidden">
        {/* Subtle radial gradient for right side */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#10b981]/5 rounded-full blur-[150px] pointer-events-none" />
        
        <div className="w-full max-w-[420px] animate-in fade-in slide-in-from-bottom-4 duration-700 mt-12 sm:mt-0 relative z-10">
          {/* Mobile logo */}
          <div className="md:hidden flex items-center gap-2 mb-10 justify-center">
            <img src="/logo.ico" alt="RetrievaAI Logo" className="w-16 h-16 object-contain drop-shadow-md" />
            <span className="font-bold text-lg tracking-wider uppercase text-white">RetrievaAI</span>
          </div>
          
          {children}
          
        </div>
      </div>
    </div>
  );
}
