import React from 'react'
import {
  ShieldCheck,
  Activity,
  Video,
  Radio,
  Navigation,
  Building2,
  Circle,
  CheckCircle2
} from 'lucide-react'

export const MapLegend: React.FC = () => {
  return (
    <div className='absolute bottom-3 left-3 z-20 bg-command-panel/95 backdrop-blur-md border border-command-border/80 rounded-lg p-2.5 shadow-xl text-[10px] font-mono select-none pointer-events-auto flex flex-col gap-2 min-w-[180px]'>
      <div className='flex items-center gap-1.5'>
        <span className='w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#00F0FF]' />
        <span className='text-slate-300'>A* AI Route</span>
      </div>

      <div className='flex items-center gap-1.5'>
        <span className='w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#10B981]' />
        <span className='text-slate-300'>Green Corridor</span>
      </div>

      <div className='flex items-center gap-1.5'>
        <span className='w-2.5 h-2.5 rounded-full bg-red-400 shadow-[0_0_8px_#EF4444]' />
        <span className='text-slate-300'>High Congestion</span>
      </div>

      <div className='flex items-center gap-1.5'>
        <span className='w-2.5 h-2.5 rounded-full bg-amber-400' />
        <span className='text-slate-300'>Medium Congestion</span>
      </div>

      <div className='flex items-center gap-1.5 border-t border-slate-700 pt-2'>
        <Video className='w-3 h-3 text-cyan-400' />
        <span className='text-slate-400'>Traffic Camera (CCTV)</span>
      </div>

      <div className='flex items-center gap-1.5'>
        <Radio className='w-3 h-3 text-emerald-400' />
        <span className='text-slate-400'>Junction Camera (Ambulance)</span>
      </div>

      <div className='flex items-center gap-1.5 border-t border-slate-700 pt-2'>
        <ShieldCheck className='w-3 h-3 text-emerald-400' />
        <span className='text-slate-400'>Adaptive Signal</span>
      </div>

      <div className='flex items-center gap-1.5 border-t border-slate-700 pt-2'>
        <span className='text-slate-400'>Signal States:</span>
      </div>

      <div className='flex flex-col gap-0.5 pl-6 text-[9px]'>
        <div className='flex items-center gap-1.5'>
          <span className='w-2 h-2 rounded-full bg-emerald-400 animate-pulse' />
          <span className='text-emerald-400'>ACTIVE (Priority Green)</span>
        </div>
        <div className='flex items-center gap-1.5'>
          <span className='w-2 h-2 rounded-full bg-emerald-300' />
          <span className='text-emerald-300'>PRIORITY (Prepared)</span>
        </div>
        <div className='flex items-center gap-1.5'>
          <span className='w-2 h-2 rounded-full bg-cyan-400' />
          <span className='text-cyan-400'>UPCOMING</span>
        </div>
        <div className='flex items-center gap-1.5'>
          <span className='w-2 h-2 rounded-full bg-slate-500' />
          <span className='text-slate-500'>PASSED</span>
        </div>
        <div className='flex items-center gap-1.5'>
          <span className='w-2 h-2 rounded-full bg-blue-400' />
          <span className='text-blue-400'>RESTORED</span>
        </div>
        <div className='flex items-center gap-1.5'>
          <span className='w-2 h-2 rounded-full bg-slate-600' />
          <span className='text-slate-500'>NORMAL</span>
        </div>
      </div>
    </div>
  )
}
