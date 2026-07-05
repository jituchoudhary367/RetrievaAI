"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';

export function DeveloperSection() {
  const [copied, setCopied] = useState(false);

  const codeSnippet = `import { RetrievaClient } from '@retrieva/sdk';

const client = new RetrievaClient({
  apiKey: process.env.RETRIEVA_API_KEY,
  environment: 'production'
});

// Stream a semantic query with inline citations
const response = await client.queries.stream({
  text: "How is the ingestion pipeline secured?",
  hybridSearch: true,
  filters: { tenantId: "tenant_abc123" }
});

for await (const chunk of response) {
  process.stdout.write(chunk.text);
}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(codeSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="developers" className="py-24 bg-[#05070B] border-b border-[rgba(255,255,255,0.04)]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="flex flex-col lg:flex-row gap-12 lg:gap-24 items-start">
          
          {/* LEFT: Content */}
          <div className="flex-1 lg:max-w-md">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="text-3xl font-medium tracking-tight text-white mb-6">
                Developer Protocol
              </h2>
              
              <p className="text-[#94A3B8] text-sm mb-8 leading-relaxed font-normal">
                Integration takes minutes, not weeks. Our APIs are designed around standard REST principles with native support for server-sent events (SSE) and strongly typed SDKs.
              </p>

              <div className="space-y-4 font-mono text-[11px] text-[#94A3B8]">
                <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.06)] pb-2">
                  <span>Authentication</span>
                  <span className="text-white">Bearer Token</span>
                </div>
                <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.06)] pb-2">
                  <span>Streaming</span>
                  <span className="text-white">SSE (Server-Sent Events)</span>
                </div>
                <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.06)] pb-2">
                  <span>Rate Limiting</span>
                  <span className="text-white">10,000 req / minute</span>
                </div>
                <div className="flex items-center justify-between pb-2">
                  <span>SDKs</span>
                  <span className="text-white">TypeScript, Python, Go</span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* RIGHT: Pure Terminal */}
          <div className="flex-1 w-full relative">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="bg-[#0A0F14] border border-[rgba(255,255,255,0.06)] overflow-hidden"
            >
              <div className="h-10 bg-[#05070B] border-b border-[rgba(255,255,255,0.06)] flex items-center justify-between px-4">
                <span className="text-[10px] font-mono text-[#94A3B8]">query.ts</span>
                <button 
                  onClick={handleCopy} 
                  className="text-[10px] font-mono text-[#94A3B8] hover:text-white uppercase tracking-wider"
                >
                  {copied ? '[ Copied ]' : '[ Copy ]'}
                </button>
              </div>

              <div className="p-6 overflow-x-auto font-mono text-xs leading-loose text-[#94A3B8]">
                <pre>
<span className="text-[#10B981]">import</span> {'{'} RetrievaClient {'}'} <span className="text-[#10B981]">from</span> <span className="text-white">'@retrieva/sdk'</span>;{'\n\n'}
<span className="text-[#10B981]">const</span> client = <span className="text-[#10B981]">new</span> RetrievaClient({'{\n'}
{'  '}apiKey: process.env.RETRIEVA_API_KEY,{'\n'}
{'  '}environment: <span className="text-white">'production'</span>{'\n'}
{'}'});{'\n\n'}
<span className="text-[rgba(255,255,255,0.3)]">// Stream a semantic query with inline citations</span>{'\n'}
<span className="text-[#10B981]">const</span> response = <span className="text-[#10B981]">await</span> client.queries.stream({'{\n'}
{'  '}text: <span className="text-white">"How is the ingestion pipeline secured?"</span>,{'\n'}
{'  '}hybridSearch: <span className="text-[#10B981]">true</span>,{'\n'}
{'  '}filters: {'{'} tenantId: <span className="text-white">"tenant_abc123"</span> {'}'}{'\n'}
{'}'});{'\n\n'}
<span className="text-[#10B981]">for await</span> (<span className="text-[#10B981]">const</span> chunk <span className="text-[#10B981]">of</span> response) {'{\n'}
{'  '}process.stdout.write(chunk.text);{'\n'}
{'}'}
                </pre>
              </div>
            </motion.div>
          </div>

        </div>
      </div>
    </section>
  );
}
