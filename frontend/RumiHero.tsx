import React, {useEffect, useRef} from 'react';
import {ArrowDown, ArrowUpRight} from 'lucide-react';
import gsap from 'gsap';
import {ScrollTrigger} from 'gsap/ScrollTrigger';
import Lenis from 'lenis';
import monument from './assets/rumi-darwaza.webp';
import './rumi-hero.css';

gsap.registerPlugin(ScrollTrigger);
type Props = {onReport: () => void; onTrack: () => void; citizen: boolean};

export default function RumiHero({onReport, onTrack, citizen}: Props) {
  const root = useRef<HTMLElement>(null);
  const ending = useRef<HTMLDivElement>(null);
  const scrolling = useRef<Lenis | null>(null);
  useEffect(() => {
    const element = root.current!;
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      if (ending.current) ending.current.inert = true;
      const lenis = new Lenis({duration: .85, smoothWheel: true, syncTouch: false});
      scrolling.current = lenis;
      const tick = (time: number) => lenis.raf(time * 1000);
      lenis.on('scroll', ScrollTrigger.update);
      gsap.ticker.add(tick);
      const timeline = gsap.timeline({scrollTrigger: {
        trigger: element, start: 'top top', end: 'bottom bottom', scrub: .65,
        invalidateOnRefresh: true,
        onUpdate: self => {
          const visible = self.progress > .66;
          if (ending.current) ending.current.inert = !visible;
        },
      }});
      timeline.to('.rumi-title', {yPercent: -55, opacity: 0, duration: .25}, 0)
        .to('.rumi-camera', {scale: 1.65, duration: .8, ease: 'power1.inOut'}, 0)
        .to('.rumi-caption', {opacity: 0, duration: .15}, .08)
        .to('.rumi-shortcut', {autoAlpha: 0, duration: .15}, .3)
        .fromTo('.rumi-veil', {clipPath: 'ellipse(0% 0% at 51% 61%)'}, {clipPath: 'ellipse(150% 150% at 51% 61%)', opacity: 1, duration: .35, ease: 'power2.in'}, .4)
        .fromTo('.rumi-arrival', {opacity: 0, y: 35, scale: .96}, {opacity: 1, y: 0, scale: 1, duration: .3}, .65);
      const image = element.querySelector('img');
      const refresh = () => ScrollTrigger.refresh();
      image?.addEventListener('load', refresh);
      return () => {
        image?.removeEventListener('load', refresh);
        timeline.scrollTrigger?.kill(); timeline.kill();
        gsap.ticker.remove(tick); lenis.destroy();
        scrolling.current = null;
        if (ending.current) ending.current.inert = false;
      };
    }, element);
    return () => media.revert();
  }, []);

  function enter() {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const rect = root.current!.getBoundingClientRect();
    const top = window.scrollY + rect.top + root.current!.offsetHeight - window.innerHeight + 32;
    if (scrolling.current) scrolling.current.scrollTo(top, {duration: 1.3, force: true});
    else window.scrollTo({top, behavior: reduced ? 'instant' : 'smooth'});
  }
  return <section ref={root} className="rumi-journey" aria-label="Rumi Darwaza: a gateway to caring for Lucknow">
    <div className="rumi-stage">
      <div className="rumi-camera" aria-hidden="true">
        <img className="rumi-image" src={monument} alt="" fetchPriority="high" width="2200" height="1467"/>
        <div className="rumi-light"/>
      </div>
      <div className="rumi-grading" aria-hidden="true"/>
      <div className="rumi-title">
        <span className="rumi-kicker">UTTAR PRADESH · INDIA</span>
        <h1>Lucknow<span>Every street has a story.</span></h1>
      </div>
      <div className="rumi-caption"><span>RUMI DARWAZA<small>A gateway. A shared responsibility.</small></span><button onClick={enter}>Enter our city <ArrowDown size={17}/></button></div>
      <div className="rumi-veil" aria-hidden="true"/>
      <div ref={ending} className="rumi-arrival">
        <span className="rumi-kicker">मेरा शहर, मेरी ज़िम्मेदारी</span>
        <h2>Lucknow.<br/><em>Ours to care for.</em></h2>
        <p>Beyond its beautiful gateways are the streets we call home.<br className="rumi-desktop"/> Make them cleaner, safer, and better. One report at a time.</p>
        <div className="rumi-actions"><button onClick={onReport}>{citizen ? 'Report an issue' : 'Open your work queue'}<ArrowUpRight size={19}/></button><button onClick={onTrack}>Track reports <ArrowUpRight size={17}/></button></div>
        <span className="rumi-signoff">JAN SAMADHAN · जन समाधान</span>
      </div>
      <button className="rumi-shortcut" onClick={onReport}>{citizen ? 'Report an issue' : 'Work queue'} <ArrowUpRight size={14}/></button>
    </div>
  </section>;
}
