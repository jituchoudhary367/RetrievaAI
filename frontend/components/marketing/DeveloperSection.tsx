"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Play, TerminalSquare, Copy, Check } from 'lucide-react';

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

export function DeveloperSection() {
  const [copied, setCopied] = useState(false);

  const codeSnippet = `import requests
import json

url = "https://api.retrieva.ai/v1/query"

payload = {
    "query": "How do I configure the indexing pipeline?",
    "stream": True,
    "hybrid_search": True,
    "top_k": 5
}
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, stream=True)

for chunk in response.iter_content(chunk_size=None):
    if chunk:
        print(chunk.decode(), end='', flush=True)`;

  const handleCopy = () => {
    navigator.clipboard.writeText(codeSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="developers" className="py-24 bg-[#05070B] border-t border-[rgba(255,255,255,0.02)] relative overflow-hidden">
      
      {/* Glow */}
      <div className="absolute top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] w-[800px] h-[400px] bg-[#10B981]/5 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />

      <div className="container mx-auto px-6 max-w-7xl relative z-10">
        <div className="flex flex-col lg:flex-row items-center gap-16">
          
          {/* LEFT: Content */}
          <div className="flex-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5 }}
            >
              <div className="inline-flex items-center rounded-full border border-[rgba(255,255,255,0.06)] bg-[#10161E] px-4 py-1.5 text-xs font-semibold text-[#94A3B8] mb-6">
                <TerminalSquare className="w-3 h-3 mr-2 text-[#10B981]" />
                Developer First
              </div>
              
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-6">
                Built for Developers
              </h2>
              
              <p className="text-[#94A3B8] text-lg mb-8 max-w-xl">
                Integrate powerful RAG capabilities into your applications in minutes. Engineered with modern standards for seamless deployment.
              </p>

              <div className="grid grid-cols-2 gap-4 mb-10">
                {['REST APIs', 'Streaming Responses', 'Python SDK', 'FastAPI', 'Docker', 'Self Hosted'].map((item) => (
                  <div key={item} className="flex items-center text-white font-medium">
                    <CheckCircle2 className="w-5 h-5 mr-3 text-[#10B981]" />
                    {item}
                  </div>
                ))}
              </div>

              <a href="https://github.com" target="_blank" rel="noopener noreferrer">
                <Button className="h-12 px-8 rounded-full bg-[#10161E] border border-[rgba(255,255,255,0.1)] hover:bg-[#1A222C] text-white transition-all shadow-sm">
                  <GithubIcon className="w-5 h-5 mr-2" />
                  Star on GitHub
                </Button>
              </a>
            </motion.div>
          </div>

          {/* RIGHT: Code Editor */}
          <div className="flex-1 w-full max-w-2xl lg:max-w-none perspective-1000">
            <motion.div
              initial={{ opacity: 0, rotateY: 10, scale: 0.95 }}
              whileInView={{ opacity: 1, rotateY: 0, scale: 1 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="bg-[#1E1E1E] rounded-xl overflow-hidden border border-[rgba(255,255,255,0.1)] shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex flex-col"
            >
              {/* VS Code Header */}
              <div className="h-12 bg-[#2D2D2D] border-b border-[#3D3D3D] flex items-center justify-between px-4">
                <div className="flex items-center gap-4">
                  <div className="flex space-x-1.5">
                    <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
                    <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                    <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
                  </div>
                  <div className="flex bg-[#1E1E1E] px-4 py-1.5 rounded-t-lg items-center border-t border-l border-r border-[#3D3D3D] translate-y-[1px]">
                    <span className="text-[#519ABA] text-xs mr-2"></span>
                    <span className="text-[#CCCCCC] text-xs font-mono">query.py</span>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <button onClick={handleCopy} className="text-[#858585] hover:text-white transition-colors" title="Copy code">
                    {copied ? <Check className="w-4 h-4 text-[#10B981]" /> : <Copy className="w-4 h-4" />}
                  </button>
                  <button className="flex items-center text-xs font-mono text-white bg-[#10B981]/20 hover:bg-[#10B981]/30 border border-[#10B981]/50 px-2 py-1 rounded transition-colors">
                    <Play className="w-3 h-3 mr-1 fill-current" /> Run
                  </button>
                </div>
              </div>

              {/* Code Content */}
              <div className="p-4 overflow-x-auto bg-[#1E1E1E] font-mono text-sm leading-relaxed">
                <pre className="text-[#D4D4D4]">
<span className="text-[#C586C0]">import</span> requests{'\n'}
<span className="text-[#C586C0]">import</span> json{'\n'}
{'\n'}
<span className="text-[#9CDCFE]">url</span> = <span className="text-[#CE9178]">"https://api.retrieva.ai/v1/query"</span>{'\n'}
{'\n'}
<span className="text-[#9CDCFE]">payload</span> = {'{'}{'\n'}
    <span className="text-[#CE9178]">"query"</span>: <span className="text-[#CE9178]">"How do I configure the indexing pipeline?"</span>,{'\n'}
    <span className="text-[#CE9178]">"stream"</span>: <span className="text-[#569CD6]">True</span>,{'\n'}
    <span className="text-[#CE9178]">"hybrid_search"</span>: <span className="text-[#569CD6]">True</span>,{'\n'}
    <span className="text-[#CE9178]">"top_k"</span>: <span className="text-[#B5CEA8]">5</span>{'\n'}
{'}'}{'\n'}
<span className="text-[#9CDCFE]">headers</span> = {'{'}{'\n'}
    <span className="text-[#CE9178]">"Authorization"</span>: <span className="text-[#CE9178]">"Bearer YOUR_API_KEY"</span>,{'\n'}
    <span className="text-[#CE9178]">"Content-Type"</span>: <span className="text-[#CE9178]">"application/json"</span>{'\n'}
{'}'}{'\n'}
{'\n'}
<span className="text-[#9CDCFE]">response</span> = requests.<span className="text-[#DCDCAA]">post</span>(url, json=payload, headers=headers, stream=<span className="text-[#569CD6]">True</span>){'\n'}
{'\n'}
<span className="text-[#C586C0]">for</span> chunk <span className="text-[#C586C0]">in</span> response.<span className="text-[#DCDCAA]">iter_content</span>(chunk_size=<span className="text-[#569CD6]">None</span>):{'\n'}
    <span className="text-[#C586C0]">if</span> chunk:{'\n'}
        <span className="text-[#DCDCAA]">print</span>(chunk.<span className="text-[#DCDCAA]">decode</span>(), end=<span className="text-[#CE9178]">''</span>, flush=<span className="text-[#569CD6]">True</span>)
                </pre>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
