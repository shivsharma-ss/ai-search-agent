import React, { useEffect, useRef } from 'react'

export default function Starfield({ density = 120 }: { density?: number }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const animRef = useRef<number | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current!
    const ctx = canvas.getContext('2d')!

    let width = (canvas.width = canvas.offsetWidth)
    let height = (canvas.height = canvas.offsetHeight)

    function onResize() {
      width = canvas.width = canvas.offsetWidth
      height = canvas.height = canvas.offsetHeight
      create()
    }

    const stars: { x: number; y: number; z: number; r: number; vx: number; vy: number; tw: number }[] = []

    function rand(a: number, b: number) { return a + Math.random() * (b - a) }

    function create() {
      stars.length = 0
      const n = Math.floor((width * height) / 15000) + density
      for (let i = 0; i < n; i++) {
        stars.push({
          x: Math.random() * width,
          y: Math.random() * height,
          z: Math.random() * 1 + 0.3,
          r: Math.random() * 1.2 + 0.2,
          vx: (Math.random() - 0.5) * 0.05,
          vy: Math.random() * 0.15 + 0.05,
          tw: Math.random() * 2 * Math.PI,
        })
      }
    }

    function loop() {
      ctx.clearRect(0, 0, width, height)
      for (const s of stars) {
        s.y += s.vy
        s.x += s.vx
        if (s.y > height) { s.y = -5; s.x = Math.random() * width }
        s.tw += 0.02
        const alpha = 0.5 + Math.sin(s.tw) * 0.4
        ctx.beginPath()
        ctx.fillStyle = `rgba(200, 230, 255, ${alpha * 0.6})`
        ctx.arc(s.x, s.y, s.r * s.z, 0, Math.PI * 2)
        ctx.fill()
      }
      animRef.current = requestAnimationFrame(loop)
    }

    create()
    loop()
    window.addEventListener('resize', onResize)
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current)
      window.removeEventListener('resize', onResize)
    }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none"/>
}
