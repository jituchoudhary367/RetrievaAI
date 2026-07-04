import React from 'react';
import { Navbar } from '@/components/marketing/Navbar';
import { HeroSection } from '@/components/marketing/HeroSection';
import { TrustedTechSection } from '@/components/marketing/TrustedTechSection';
import { ComparisonSection } from '@/components/marketing/ComparisonSection';
import { TimelineSection } from '@/components/marketing/TimelineSection';
import { FeaturesSection } from '@/components/marketing/FeaturesSection';
import { DeveloperSection } from '@/components/marketing/DeveloperSection';
import { TestimonialsSection } from '@/components/marketing/TestimonialsSection';
import { CtaSection } from '@/components/marketing/CtaSection';
import { Footer } from '@/components/marketing/Footer';

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[#05070B] text-white font-sans selection:bg-[#10B981]/30">
      <Navbar />
      <main className="flex-grow">
        <HeroSection />
        <TrustedTechSection />
        <ComparisonSection />
        <TimelineSection />
        <FeaturesSection />
        <DeveloperSection />
        <TestimonialsSection />
        <CtaSection />
      </main>
      <Footer />
    </div>
  );
}
