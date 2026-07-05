"use client";

import React from 'react';
import Link from 'next/link';

export function Footer() {
  return (
    <footer className="bg-[#05070B]">
      <div className="container mx-auto px-6 max-w-7xl">
        
        {/* Main Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-px bg-[rgba(255,255,255,0.04)] border-l border-r border-[rgba(255,255,255,0.04)]">
          
          {/* Brand Info */}
          <div className="md:col-span-12 lg:col-span-5 bg-[#05070B] p-8 lg:p-12 border-b border-[rgba(255,255,255,0.04)] lg:border-b-0">
            <Link href="/" className="flex items-center space-x-2 group mb-6">
              <div className="w-5 h-5 relative flex items-center justify-center opacity-90 group-hover:opacity-100 transition-opacity">
                <img src="/logo.png" alt="RetrievaAI Logo" className="w-5 h-5 object-contain" />
              </div>
              <span className="font-semibold text-white tracking-tight text-sm">RetrievaAI</span>
            </Link>
            <p className="text-[#94A3B8] text-[11px] font-mono leading-relaxed max-w-xs">
              Enterprise Retrieval Augmented Generation. Secure, self-hosted, scalable semantic infrastructure.
            </p>
          </div>

          {/* Links 1 */}
          <div className="md:col-span-4 lg:col-span-2 bg-[#0A0F14] p-8 lg:p-12 border-b md:border-b-0 border-[rgba(255,255,255,0.04)]">
            <h4 className="text-white text-[10px] font-mono uppercase tracking-widest mb-6">Product</h4>
            <ul className="space-y-4">
              {['Platform', 'Infrastructure', 'Security'].map(link => (
                <li key={link}>
                  <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors text-xs">{link}</Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Links 2 */}
          <div className="md:col-span-4 lg:col-span-2 bg-[#05070B] p-8 lg:p-12 border-b md:border-b-0 border-[rgba(255,255,255,0.04)]">
            <h4 className="text-white text-[10px] font-mono uppercase tracking-widest mb-6">Developers</h4>
            <ul className="space-y-4">
              {['Documentation', 'API Reference', 'GitHub'].map(link => (
                <li key={link}>
                  <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors text-xs">{link}</Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Links 3 */}
          <div className="md:col-span-4 lg:col-span-3 bg-[#0A0F14] p-8 lg:p-12">
            <h4 className="text-white text-[10px] font-mono uppercase tracking-widest mb-6">Company</h4>
            <ul className="space-y-4">
              {['About', 'Careers', 'Contact'].map(link => (
                <li key={link}>
                  <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors text-xs">{link}</Link>
                </li>
              ))}
            </ul>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="border-t border-l border-r border-[rgba(255,255,255,0.04)] bg-[#05070B] p-8 flex flex-col sm:flex-row items-center justify-between">
          <div className="text-[10px] font-mono text-[#94A3B8] uppercase tracking-widest">
            © 2026 RetrievaAI
          </div>
          <div className="flex space-x-6 mt-4 sm:mt-0 text-[10px] font-mono uppercase tracking-widest">
            <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors">Privacy</Link>
            <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors">Terms</Link>
            <Link href="#" className="text-[#94A3B8] hover:text-white transition-colors">Status</Link>
          </div>
        </div>

      </div>
    </footer>
  );
}
