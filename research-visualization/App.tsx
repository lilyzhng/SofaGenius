
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/

import React, { useState, useEffect } from 'react';
import { HeroScene, QuantumComputerScene } from './components/QuantumScene';
import { SurfaceCodeDiagram, TransformerDecoderDiagram, PerformanceMetricDiagram } from './components/Diagrams';
import { ArrowDown, Menu, X, BookOpen } from 'lucide-react';

const AuthorCard = ({ name, role, delay }: { name: string, role: string, delay: string }) => {
  return (
    <div className="flex flex-col group animate-fade-in-up items-center p-8 bg-white rounded-xl border border-stone-200 shadow-sm hover:shadow-md transition-all duration-300 w-full max-w-xs hover:border-nobel-gold/50" style={{ animationDelay: delay }}>
      <h3 className="font-serif text-2xl text-stone-900 text-center mb-3">{name}</h3>
      <div className="w-12 h-0.5 bg-nobel-gold mb-4 opacity-60"></div>
      <p className="text-xs text-stone-500 font-bold uppercase tracking-widest text-center leading-relaxed">{role}</p>
    </div>
  );
};

const App: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    setMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      // Account for fixed header offset
      const headerOffset = 100;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth"
      });
    }
  };

  return (
    <div className="min-h-screen bg-[#F9F8F4] text-stone-800 selection:bg-nobel-gold selection:text-white">
      
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-[#F9F8F4]/90 backdrop-blur-md shadow-sm py-4' : 'bg-transparent py-6'}`}>
        <div className="container mx-auto px-6 flex justify-between items-center">
          <div className="flex items-center gap-4 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-8 h-8 bg-nobel-gold rounded-full flex items-center justify-center text-white font-serif font-bold text-xl shadow-sm pb-1">α</div>
            <span className={`font-serif font-bold text-lg tracking-wide transition-opacity ${scrolled ? 'opacity-100' : 'opacity-0 md:opacity-100'}`}>
              ALPHAQUBIT <span className="font-normal text-stone-500">2024</span>
            </span>
          </div>
          
          <div className="hidden md:flex items-center gap-8 text-sm font-medium tracking-wide text-stone-600">
            <a href="#introduction" onClick={scrollToSection('introduction')} className="hover:text-nobel-gold transition-colors cursor-pointer uppercase">Introduction</a>
            <a href="#science" onClick={scrollToSection('science')} className="hover:text-nobel-gold transition-colors cursor-pointer uppercase">The Surface Code</a>
            <a href="#impact" onClick={scrollToSection('impact')} className="hover:text-nobel-gold transition-colors cursor-pointer uppercase">Impact</a>
            <a href="#authors" onClick={scrollToSection('authors')} className="hover:text-nobel-gold transition-colors cursor-pointer uppercase">Authors</a>
            <a 
              href="https://doi.org/10.1038/s41586-024-08148-8" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="px-5 py-2 bg-stone-900 text-white rounded-full hover:bg-stone-800 transition-colors shadow-sm cursor-pointer"
            >
              View Paper
            </a>
          </div>

          <button className="md:hidden text-stone-900 p-2" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X /> : <Menu />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="fixed inset-0 z-40 bg-[#F9F8F4] flex flex-col items-center justify-center gap-8 text-xl font-serif animate-fade-in">
            <a href="#introduction" onClick={scrollToSection('introduction')} className="hover:text-nobel-gold transition-colors cursor-pointer uppercase">Introduction</a>
            <a href="#science" onClick={scrollToSection('science')} className="hover:text-nobel-gold transition-colors cursor-pointer uppercase">The Science</a>
            <a href="#impact" onClick={scrollToSection('impact')} className="hover:text-nobel-gold transition-colors cursor-pointer uppercase">Impact</a>
            <a href="#authors" onClick={scrollToSection('authors')} className="hover:text-nobel-gold transition-colors cursor-pointer uppercase">Authors</a>
            <a 
              href="https://doi.org/10.1038/s41586-024-08148-8" 
              target="_blank" 
              rel="noopener noreferrer" 
              onClick={() => setMenuOpen(false)} 
              className="px-6 py-3 bg-stone-900 text-white rounded-full shadow-lg cursor-pointer"
            >
              View Paper
            </a>
        </div>
      )}

      {/* Hero Section */}
      <header className="relative h-screen flex items-center justify-center overflow-hidden">
        <HeroScene />
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 z-0 pointer-events-none bg-[radial-gradient(circle_at_center,rgba(249,248,244,0.92)_0%,rgba(249,248,244,0.6)_50%,rgba(249,248,244,0.3)_100%)]" />

        <div className="relative z-10 container mx-auto px-6 text-center">
          <div className="inline-block mb-4 px-3 py-1 border border-nobel-gold text-nobel-gold text-xs tracking-[0.2em] uppercase font-bold rounded-full backdrop-blur-sm bg-white/30">
            Nature • Nov 2024
          </div>
          <h1 className="font-serif text-5xl md:text-7xl lg:text-9xl font-medium leading-tight md:leading-[0.9] mb-8 text-stone-900 drop-shadow-sm">
            AlphaQubit <br/><span className="italic font-normal text-stone-600 text-3xl md:text-5xl block mt-4">AI for Quantum Error Correction</span>
          </h1>
          <p className="max-w-2xl mx-auto text-lg md:text-xl text-stone-700 font-light leading-relaxed mb-12">
            A recurrent, transformer-based neural network that learns to decode the surface code with unprecedented accuracy.
          </p>
          
          <div className="flex justify-center">
             <a href="#introduction" onClick={scrollToSection('introduction')} className="group flex flex-col items-center gap-2 text-sm font-medium text-stone-500 hover:text-stone-900 transition-colors cursor-pointer">
                <span>DISCOVER</span>
                <span className="p-2 border border-stone-300 rounded-full group-hover:border-stone-900 transition-colors bg-white/50">
                    <ArrowDown size={16} />
                </span>
             </a>
          </div>
        </div>
      </header>

      <main>
        {/* Introduction */}
        <section id="introduction" className="py-24 bg-white">
          <div className="container mx-auto px-6 md:px-12 grid grid-cols-1 md:grid-cols-12 gap-12 items-start">
            <div className="md:col-span-4">
              <div className="inline-block mb-3 text-xs font-bold tracking-widest text-stone-500 uppercase">Introduction</div>
              <h2 className="font-serif text-4xl mb-6 leading-tight text-stone-900">The Noise Barrier</h2>
              <div className="w-16 h-1 bg-nobel-gold mb-6"></div>
            </div>
            <div className="md:col-span-8 text-lg text-stone-600 leading-relaxed space-y-6">
              <p>
                <span className="text-5xl float-left mr-3 mt-[-8px] font-serif text-nobel-gold">B</span>uilding a large-scale quantum computer requires correcting the errors that inevitably arise in physical systems. The state of the art is the <strong>surface code</strong>, which encodes information redundantly across many physical qubits.
              </p>
              <p>
                However, interpreting the noisy signals from these codes—a task called "decoding"—is a massive challenge. Complex noise effects like cross-talk and leakage confuse standard algorithms. <strong className="text-stone-900 font-medium">AlphaQubit</strong> uses machine learning to learn these complex error patterns directly from the quantum processor, achieving accuracy far beyond human-designed algorithms.
              </p>
            </div>
          </div>
        </section>

        {/* The Science: Surface Code */}
        <section id="science" className="py-24 bg-white border-t border-stone-100">
            <div className="container mx-auto px-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-stone-100 text-stone-600 text-xs font-bold tracking-widest uppercase rounded-full mb-6 border border-stone-200">
                            <BookOpen size={14}/> THE SYSTEM
                        </div>
                        <h2 className="font-serif text-4xl md:text-5xl mb-6 text-stone-900">The Surface Code</h2>
                        <p className="text-lg text-stone-600 mb-6 leading-relaxed">
                           In a surface code, "Data Qubits" hold the quantum information, while "Stabilizer Qubits" interspersed between them act as watchdogs. They measure parity checks (X and Z type) to detect errors without destroying the quantum state.
                        </p>
                        <p className="text-lg text-stone-600 mb-6 leading-relaxed">
                            When a data qubit flips, adjacent stabilizers light up. The pattern of these lights is the "syndrome." The decoder's job is to look at the syndrome and guess which data qubit flipped.
                        </p>
                    </div>
                    <div>
                        <SurfaceCodeDiagram />
                    </div>
                </div>
            </div>
        </section>

        {/* The Science: Transformer Decoder */}
        <section className="py-24 bg-stone-900 text-stone-100 overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
                {/* Decorative background pattern - Gold/Stone theme */}
                <div className="w-96 h-96 rounded-full bg-stone-600 blur-[100px] absolute top-[-100px] left-[-100px]"></div>
                <div className="w-96 h-96 rounded-full bg-nobel-gold blur-[100px] absolute bottom-[-100px] right-[-100px]"></div>
            </div>

            <div className="container mx-auto px-6 relative z-10">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                     <div className="order-2 lg:order-1">
                        <TransformerDecoderDiagram />
                     </div>
                     <div className="order-1 lg:order-2">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-stone-800 text-nobel-gold text-xs font-bold tracking-widest uppercase rounded-full mb-6 border border-stone-700">
                            THE INNOVATION
                        </div>
                        <h2 className="font-serif text-4xl md:text-5xl mb-6 text-white">Neural Decoding</h2>
                        <p className="text-lg text-stone-400 mb-6 leading-relaxed">
                            Standard decoders assume simple, independent errors. Real hardware is messier. AlphaQubit treats decoding as a sequence prediction problem, using a <strong>Recurrent Transformer</strong> architecture.
                        </p>
                        <p className="text-lg text-stone-400 leading-relaxed">
                            It ingests the history of stabilizer measurements and uses "soft" analog information—probabilities rather than just binary 0s and 1s—to make highly informed predictions about logical errors.
                        </p>
                     </div>
                </div>
            </div>
        </section>

        {/* The Science: Results */}
        <section className="py-24 bg-[#F9F8F4]">
            <div className="container mx-auto px-6">
                <div className="max-w-4xl mx-auto text-center mb-12">
                    <h2 className="font-serif text-4xl md:text-5xl mb-6 text-stone-900">Outperforming the Standard</h2>
                    <p className="text-lg text-stone-600 leading-relaxed">
                        AlphaQubit was tested on Google's Sycamore processor and accurate simulations. It consistently outperforms "Minimum-Weight Perfect Matching" (MWPM), the industry standard, effectively making the quantum computer appear cleaner than it actually is.
                    </p>
                </div>
                <div className="max-w-3xl mx-auto">
                    <PerformanceMetricDiagram />
                </div>
            </div>
        </section>

        {/* Impact */}
        <section id="impact" className="py-24 bg-white border-t border-stone-200">
             <div className="container mx-auto px-6 grid grid-cols-1 md:grid-cols-12 gap-12">
                <div className="md:col-span-5 relative">
                    <div className="aspect-square bg-[#F5F4F0] rounded-xl overflow-hidden relative border border-stone-200 shadow-inner">
                        <QuantumComputerScene />
                        <div className="absolute bottom-4 left-0 right-0 text-center text-xs text-stone-400 font-serif italic">Simulation of the Sycamore Processor environment</div>
                    </div>
                </div>
                <div className="md:col-span-7 flex flex-col justify-center">
                    <div className="inline-block mb-3 text-xs font-bold tracking-widest text-stone-500 uppercase">IMPACT</div>
                    <h2 className="font-serif text-4xl mb-6 text-stone-900">Towards Fault Tolerance</h2>
                    <p className="text-lg text-stone-600 mb-6 leading-relaxed">
                        AlphaQubit maintains its advantage even as the code distance increases (up to distance 11). It handles realistic noise including cross-talk and leakage, effects that often cripple standard decoders.
                    </p>
                    <p className="text-lg text-stone-600 mb-8 leading-relaxed">
                        By learning from data directly, machine learning decoders can adapt to the unique quirks of each quantum processor, potentially reducing the hardware requirements for useful quantum computing.
                    </p>
                    
                    <div className="p-6 bg-[#F9F8F4] border border-stone-200 rounded-lg border-l-4 border-l-nobel-gold">
                        <p className="font-serif italic text-xl text-stone-800 mb-4">
                            "Our work illustrates the ability of machine learning to go beyond human-designed algorithms by learning from data directly, highlighting machine learning as a strong contender for decoding in quantum computers."
                        </p>
                        <span className="text-sm font-bold text-stone-500 tracking-wider uppercase">— Bausch et al., Nature (2024)</span>
                    </div>
                </div>
             </div>
        </section>

        {/* Authors */}
        <section id="authors" className="py-24 bg-[#F5F4F0] border-t border-stone-300">
           <div className="container mx-auto px-6">
                <div className="text-center mb-16">
                    <div className="inline-block mb-3 text-xs font-bold tracking-widest text-stone-500 uppercase">RESEARCH TEAM</div>
                    <h2 className="font-serif text-3xl md:text-5xl mb-4 text-stone-900">Key Contributors</h2>
                    <p className="text-stone-500 max-w-2xl mx-auto">A collaboration between Google DeepMind and Google Quantum AI.</p>
                </div>
                
                <div className="flex flex-col md:flex-row gap-8 justify-center items-center flex-wrap">
                    <AuthorCard 
                        name="Johannes Bausch" 
                        role="Google DeepMind" 
                        delay="0s" 
                    />
                    <AuthorCard 
                        name="Andrew W. Senior" 
                        role="Google DeepMind" 
                        delay="0.1s" 
                    />
                    <AuthorCard 
                        name="Francisco J. H. Heras" 
                        role="Google DeepMind" 
                        delay="0.2s" 
                    />
                    <AuthorCard 
                        name="Thomas Edlich" 
                        role="Google DeepMind" 
                        delay="0.3s" 
                    />
                    <AuthorCard 
                        name="Alex Davies" 
                        role="Google DeepMind" 
                        delay="0.4s" 
                    />
                    <AuthorCard 
                        name="Michael Newman" 
                        role="Google Quantum AI" 
                        delay="0.5s" 
                    />
                </div>
                <div className="text-center mt-12">
                    <p className="text-stone-500 italic">And many others contributing to hardware, theory, and engineering.</p>
                </div>
           </div>
        </section>

      </main>

      <footer className="bg-stone-900 text-stone-400 py-16">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="text-center md:text-left">
                <div className="text-white font-serif font-bold text-2xl mb-2">AlphaQubit</div>
                <p className="text-sm">Visualizing "Learning high-accuracy error decoding for quantum processors"</p>
            </div>
        </div>
        <div className="text-center mt-12 text-xs text-stone-600">
            Based on research published in Nature (2024). Generated by AI.
        </div>
      </footer>
    </div>
  );
};

export default App;
