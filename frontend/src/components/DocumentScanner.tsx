import { useRef, useState, useEffect } from 'react'
import { Camera, Upload, X, RotateCcw, Check, Loader2, AlertCircle, CheckCircle, ScanLine } from 'lucide-react'
import { documentsApi } from '../services/api'

export interface ScanResult {
  ocr_success: boolean
  ocr_partial?: boolean
  document_type?: string
  first_name?: string
  last_name?: string
  date_of_birth?: string
  nationality?: string
  gender?: string
  passport_number?: string
  emirates_id?: string
  document_expiry?: string
  place_of_birth?: string
}

interface DocumentScannerProps {
  onResult: (result: ScanResult) => void
  label?: string
}

// ── Camera overlay ────────────────────────────────────────────────────────────

export function CameraCapture({ onCapture, onClose }: { onCapture: (f: File) => void; onClose: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [capturedUrl, setCapturedUrl] = useState<string | null>(null)
  const [camError, setCamError] = useState('')
  const [camLoading, setCamLoading] = useState(true)

  useEffect(() => { startCamera(); return () => stopStream() }, [])

  const startCamera = async () => {
    setCamLoading(true); setCamError('')
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } },
      })
      setStream(s)
      if (videoRef.current) {
        videoRef.current.srcObject = s
        videoRef.current.onloadedmetadata = () => setCamLoading(false)
      }
    } catch (e: unknown) {
      const err = e as { name?: string }
      setCamError(
        err?.name === 'NotAllowedError'
          ? 'Camera permission denied. Please allow camera access in your browser settings.'
          : 'Camera not available on this device. Please use the file upload option instead.',
      )
      setCamLoading(false)
    }
  }

  const stopStream = () => { stream?.getTracks().forEach(t => t.stop()) }

  const capture = () => {
    if (!videoRef.current || !canvasRef.current) return
    const { videoWidth: w, videoHeight: h } = videoRef.current
    canvasRef.current.width = w; canvasRef.current.height = h
    canvasRef.current.getContext('2d')?.drawImage(videoRef.current, 0, 0)
    setCapturedUrl(canvasRef.current.toDataURL('image/jpeg', 0.92))
  }

  const usePhoto = () => {
    if (!canvasRef.current || !capturedUrl) return
    canvasRef.current.toBlob(blob => {
      if (blob) onCapture(new File([blob], 'document.jpg', { type: 'image/jpeg' }))
    }, 'image/jpeg', 0.92)
    stopStream(); onClose()
  }

  const retake = () => setCapturedUrl(null)
  const handleClose = () => { stopStream(); onClose() }

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col" style={{ touchAction: 'none' }}>
      <div className="flex items-center justify-between px-4 py-3 bg-black/80 text-white flex-shrink-0">
        <div>
          <p className="font-semibold text-sm">Scan Document</p>
          <p className="text-xs text-white/60">Position your passport or Emirates ID within the frame</p>
        </div>
        <button onClick={handleClose} className="p-2 rounded-full bg-white/10 hover:bg-white/20">
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="flex-1 relative overflow-hidden bg-black">
        {camLoading && !camError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-10 h-10 text-white animate-spin" />
            <p className="text-white/70 text-sm">Starting camera…</p>
          </div>
        )}
        {camError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-8 text-center">
            <Camera className="w-16 h-16 text-white/30" />
            <p className="text-white/80 text-sm leading-relaxed">{camError}</p>
            <button onClick={handleClose} className="px-5 py-2.5 bg-white/20 text-white rounded-xl text-sm font-semibold">
              Use File Upload Instead
            </button>
          </div>
        )}
        {!capturedUrl ? (
          <video ref={videoRef} autoPlay playsInline muted
            className="w-full h-full object-cover"
            style={{ display: camLoading || camError ? 'none' : 'block' }}
          />
        ) : (
          <img src={capturedUrl} alt="Captured document" className="w-full h-full object-contain" />
        )}
        {!capturedUrl && !camLoading && !camError && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="relative" style={{ width: '85%', aspectRatio: '1.586/1' }}>
              {[
                'top-0 left-0 border-t-4 border-l-4 rounded-tl-lg',
                'top-0 right-0 border-t-4 border-r-4 rounded-tr-lg',
                'bottom-0 left-0 border-b-4 border-l-4 rounded-bl-lg',
                'bottom-0 right-0 border-b-4 border-r-4 rounded-br-lg',
              ].map((cls, i) => (
                <div key={i} className={`absolute w-8 h-8 border-amber-400 ${cls}`} />
              ))}
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-white/60 text-xs bg-black/40 px-3 py-1.5 rounded-full">
                  Align document within frame
                </p>
              </div>
            </div>
          </div>
        )}
        <canvas ref={canvasRef} className="hidden" />
      </div>
      <div className="flex-shrink-0 bg-black/90 px-6 py-6">
        {!capturedUrl ? (
          <div className="flex items-center justify-between max-w-xs mx-auto">
            <button onClick={handleClose} className="text-white/60 text-sm font-medium px-4 py-2">
              Cancel
            </button>
            <button
              onClick={capture}
              disabled={camLoading || !!camError}
              className="w-18 h-18 flex items-center justify-center disabled:opacity-30"
              aria-label="Capture photo"
            >
              <div className="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center">
                <div className="w-12 h-12 rounded-full bg-white" />
              </div>
            </button>
            <div className="w-16" />
          </div>
        ) : (
          <div className="flex gap-3 max-w-xs mx-auto">
            <button onClick={retake}
              className="flex-1 flex items-center justify-center gap-2 py-3 bg-white/20 text-white rounded-xl text-sm font-semibold">
              <RotateCcw className="w-4 h-4" /> Retake
            </button>
            <button onClick={usePhoto}
              className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-xl text-sm font-semibold">
              <Check className="w-4 h-4" /> Use Photo
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── DocumentScanner (scan button + file upload + OCR call + status) ───────────

export default function DocumentScanner({ onResult, label }: DocumentScannerProps) {
  const [showCamera, setShowCamera] = useState(false)
  const [ocrLoading, setOcrLoading] = useState(false)
  const [ocrMsg, setOcrMsg] = useState<{ text: string; type: 'success' | 'partial' | 'error' } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    setOcrLoading(true)
    setOcrMsg(null)
    try {
      const res = await documentsApi.ocrDocument(file)
      const d: ScanResult = res.data.data
      onResult(d)
      if (d.ocr_success) {
        setOcrMsg({
          text: d.ocr_partial
            ? 'Partially scanned — some fields filled. Please verify all details.'
            : 'Document scanned. Please verify the auto-filled fields below.',
          type: d.ocr_partial ? 'partial' : 'success',
        })
      } else {
        setOcrMsg({ text: res.data.message || 'Could not read document. Please fill in details manually.', type: 'error' })
      }
    } catch {
      setOcrMsg({ text: 'Scan failed. Please fill in details manually.', type: 'error' })
    } finally {
      setOcrLoading(false)
    }
  }

  return (
    <>
      {showCamera && (
        <CameraCapture
          onCapture={file => { setShowCamera(false); handleFile(file) }}
          onClose={() => setShowCamera(false)}
        />
      )}

      <div className="mb-4">
        {label && <p className="text-xs text-gray-500 mb-2">{label}</p>}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowCamera(true)}
            disabled={ocrLoading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-blue-300 bg-blue-50 text-blue-700 text-xs font-semibold hover:bg-blue-100 transition-colors disabled:opacity-50"
          >
            <ScanLine className="w-3.5 h-3.5" />
            Scan Document
          </button>
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={ocrLoading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-200 bg-white text-gray-600 text-xs font-semibold hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload File
          </button>
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="image/*,application/pdf"
          className="hidden"
          onChange={e => {
            const f = e.target.files?.[0]
            if (f) handleFile(f)
            e.target.value = ''
          }}
        />

        {ocrLoading && (
          <div className="mt-2 flex items-center gap-2 text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin flex-shrink-0" />
            Scanning document…
          </div>
        )}
        {ocrMsg && !ocrLoading && (
          <div className={`mt-2 flex items-start gap-2 text-xs rounded-lg px-3 py-2 ${
            ocrMsg.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-700'
              : ocrMsg.type === 'partial'
              ? 'bg-amber-50 border border-amber-200 text-amber-700'
              : 'bg-red-50 border border-red-200 text-red-700'
          }`}>
            {ocrMsg.type === 'success'
              ? <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              : <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />}
            {ocrMsg.text}
          </div>
        )}
      </div>
    </>
  )
}
