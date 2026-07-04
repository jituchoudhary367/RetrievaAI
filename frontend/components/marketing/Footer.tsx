"use client";

import React from 'react';
import Link from 'next/link';
import { Hexagon, ArrowRight } from 'lucide-react';

const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.2c3-.3 6-1.5 6-6.5a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 5 3 6.2 6 6.5a4.8 4.8 0 0 0-1 3.2v4" /></svg>
);
const TwitterIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5 2.8 9 2.8 9s1.5.8 3 .5c-2.4-2-2.3-6-2.3-6s1.5 1.4 3 1.6c-2.3-2.6-1.3-7.5.5-9 3.5 4.3 9.4 6.6 15 6.6Z" /></svg>
);
const LinkedinIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" /><rect width="4" height="12" x="2" y="9" /><circle cx="4" cy="4" r="2" /></svg>
);

export function Footer() {
  return (
    <footer className="bg-[#05070B] pt-20 pb-10 border-t border-[rgba(255,255,255,0.06)] relative z-10">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 lg:gap-8 mb-16">
          
          {/* Left: Brand */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center space-x-3 group mb-6 inline-flex">
              <div className="relative flex items-center justify-center w-8 h-8">
                <Hexagon className="w-8 h-8 text-[#10B981] absolute fill-[#10B981]/20 group-hover:fill-[#10B981]/40 transition-colors" />
                <div className="w-2 h-2 bg-[#10B981] rounded-full relative z-10" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-white tracking-wide leading-tight">RetrievaAI</span>
                <span className="text-[10px] text-[#94A3B8] tracking-widest uppercase font-medium">Enterprise RAG Platform</span>
              </div>
            </Link>
            <p className="text-[#94A3B8] text-sm leading-relaxed max-w-sm mb-8">
              Retrieve. Understand. Generate. The production-ready platform for building secure and scalable AI applications powered by your knowledge.
            </p>
          </div>

          {/* Center: Links */}
          <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-3 gap-8">
            <div>
              <h4 className="text-white font-bold mb-4">Product</h4>
              <ul className="space-y-3">
                {['Features', 'Solutions', 'Updates'].map(link => (
                  <li key={link}>
                    <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors text-sm">{link}</Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Developers</h4>
              <ul className="space-y-3">
                {['API Reference', 'GitHub'].map(link => (
                  <li key={link}>
                    <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors text-sm">{link}</Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Company</h4>
              <ul className="space-y-3">
                {['About', 'Careers', 'Contact'].map(link => (
                  <li key={link}>
                    <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors text-sm">{link}</Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right: Newsletter & Socials */}
          <div className="lg:col-span-1 flex flex-col">
            <h4 className="text-white font-bold mb-4">Stay up to date</h4>
            <div className="relative mb-6">
              <input 
                type="email" 
                placeholder="Enter your email" 
                className="w-full bg-[#10161E] border border-[rgba(255,255,255,0.06)] rounded-lg py-2.5 px-4 text-sm text-white placeholder:text-[#94A3B8] focus:outline-none focus:border-[#10B981] transition-colors pr-10"
              />
              <button className="absolute right-2 top-1/2 -translate-y-1/2 text-[#94A3B8] hover:text-[#10B981] transition-colors">
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center space-x-4">
              <a href="#" className="text-[#94A3B8] hover:text-white transition-colors"><GithubIcon className="w-5 h-5" /></a>
              <a href="#" className="text-[#94A3B8] hover:text-white transition-colors"><TwitterIcon className="w-5 h-5" /></a>
              <a href="#" className="text-[#94A3B8] hover:text-white transition-colors"><LinkedinIcon className="w-5 h-5" /></a>
            </div>
          </div>

        </div>

        {/* Bottom */}
        <div className="pt-8 border-t border-[rgba(255,255,255,0.06)] flex flex-col sm:flex-row items-center justify-between text-xs text-[#94A3B8]">
          <p>© 2026 RetrievaAI. All Rights Reserved.</p>
          <div className="flex space-x-6 mt-4 sm:mt-0">
            <Link href="#" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link href="#" className="hover:text-white transition-colors">Terms of Service</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
