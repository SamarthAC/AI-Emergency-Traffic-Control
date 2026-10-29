import React, { useState, useRef } from 'react';
import { Upload, X, CheckCircle, AlertTriangle, Loader2, Sparkles, Image as ImageIcon } from 'lucide-react';
import { dashboardApi } from '../../api/dashboardApi';
import { useDashboardStore } from '../../store/dashboardStore';

interface CameraUploadModalProps {
  cameraId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CameraUploadModal: React.FC<CameraUploadModalProps> = ({
  cameraId,
  isOpen,
  onClose,
}) => {
  const { uploadStatus, setCameraUploadStatus } = useDashboardStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen || !cameraId) return null;

  const currentStatus = uploadStatus[cameraId] || 'IDLE';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['jpg', 'jpeg', 'png'].includes(ext || '')) {
      setErrorMsg('Unsupported format. Please select a .jpg, .jpeg, or .png image.');
      return;
    }

    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = () => {
      setPreviewUrl(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setErrorMsg(null);
      setCameraUploadStatus(cameraId, 'UPLOADING');

      await dashboardApi.uploadTrafficCameraImage(cameraId, selectedFile);

      // Frame saved in model/live_inputs. Python watcher will detect and run CNN inference.
      setCameraUploadStatus(cameraId, 'WAITING_CNN');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setErrorMsg(msg);
      setCameraUploadStatus(cameraId, 'IDLE');
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setErrorMsg(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-command-surface border border-command-borderLight rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-5 py-3.5 bg-command-panel border-b border-command-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-100">
              CHANGE CAMERA FRAME — {cameraId}
            </h3>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 font-mono text-xs">
          <p className="text-slate-300">
            Replace frame for <strong className="text-cyan-300 font-bold">{cameraId}</strong>? The simulated CCTV
            watcher will ingest the new frame, trigger CNN density analysis, and re-evaluate the A* corridor.
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png"
            onChange={handleFileChange}
            className="hidden"
          />

          {/* Local Preview Area */}
          {previewUrl ? (
            <div className="relative rounded-lg overflow-hidden border border-cyan-500/50 bg-black aspect-video flex items-center justify-center shadow-lg">
              <img
                src={previewUrl}
                alt="Selected frame preview"
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-2 right-2 px-2.5 py-1 bg-black/80 hover:bg-black text-cyan-300 rounded border border-cyan-500/40 text-[10px]"
              >
                Choose Different File
              </button>
            </div>
          ) : (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-command-border hover:border-cyan-500/60 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer bg-slate-900/50 hover:bg-slate-900/80 transition-all text-center gap-2"
            >
              <ImageIcon className="w-8 h-8 text-slate-500" />
              <span className="text-slate-300 font-bold">Select .jpg, .jpeg, or .png image</span>
              <span className="text-[10px] text-slate-500">
                Click to browse local files from your computer
              </span>
            </div>
          )}

          {errorMsg && (
            <div className="p-2.5 bg-red-950/80 border border-red-500/60 rounded text-red-300 text-[11px] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Upload Status Pipeline Feedback */}
          {currentStatus !== 'IDLE' && (
            <div className="p-3 bg-slate-900/90 border border-command-border rounded-lg space-y-1.5">
              <div className="text-[10px] uppercase text-slate-400 font-bold">PIPELINE EXECUTION STATUS:</div>

              {currentStatus === 'UPLOADING' && (
                <div className="flex items-center gap-2 text-cyan-400 font-bold text-[11px] animate-pulse">
                  <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                  <span>UPLOADING CAMERA FRAME...</span>
                </div>
              )}

              {currentStatus === 'WAITING_CNN' && (
                <div className="flex items-center gap-2 text-amber-400 font-bold text-[11px]">
                  <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                  <span>FRAME UPDATED — WAITING FOR CNN ANALYSIS</span>
                </div>
              )}

              {currentStatus === 'CNN_COMPLETE' && (
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-[11px]">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>CNN ANALYSIS COMPLETE</span>
                </div>
              )}

              {currentStatus === 'ROUTE_UPDATED' && (
                <div className="flex items-center gap-2 text-cyan-300 font-bold text-[11px]">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <span>ROUTE RE-EVALUATED &bull; ROUTE UPDATED</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3.5 bg-command-panel border-t border-command-border flex items-center justify-end gap-2.5">
          <button
            onClick={handleClose}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!selectedFile || currentStatus === 'UPLOADING' || currentStatus === 'WAITING_CNN'}
            className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 shadow-md"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload &amp; Analyse</span>
          </button>
        </div>
      </div>
    </div>
  );
};
