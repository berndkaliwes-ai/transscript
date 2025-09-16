import { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Upload, FileAudio, Download, CheckCircle, XCircle, AlertTriangle, Mic, FileText, BarChart3, Scissors, Clock, Type, AlignLeft } from 'lucide-react'
import './App.css'

function App() {
  const [files, setFiles] = useState([])
  const [processing, setProcessing] = useState(false)
  const [results, setResults] = useState([])
  const [dragActive, setDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [segmentationType, setSegmentationType] = useState('sentence')

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFiles = Array.from(e.dataTransfer.files)
      setFiles(prev => [...prev, ...droppedFiles])
    }
  }, [])

  const handleFileSelect = (e) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      setFiles(prev => [...prev, ...selectedFiles])
    }
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const processFiles = async () => {
    if (files.length === 0) return

    setProcessing(true)
    setUploadProgress(0)
    
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    formData.append('segmentation_type', segmentationType)

    try {
      const response = await fetch('/api/audio/upload', {
        method: 'POST',
        body: formData,
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          setUploadProgress(progress)
        }
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()
      setResults(data.results)
    } catch (error) {
      console.error('Error processing files:', error)
      setResults([{
        status: 'error',
        error: 'Fehler beim Verarbeiten der Dateien: ' + error.message
      }])
    } finally {
      setProcessing(false)
      setUploadProgress(0)
    }
  }

  const downloadCSV = async () => {
    try {
      const response = await fetch('/api/audio/export/csv', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ results })
      })

      if (!response.ok) {
        throw new Error('CSV export failed')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = 'tts_kokei_training_data.csv'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading CSV:', error)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
    }
  }

  const getQualityBadge = (assessment) => {
    if (!assessment) return null
    
    const { quality_score, transcription_suitable, voice_cloning_suitable } = assessment
    
    if (voice_cloning_suitable) {
      return <Badge variant="default" className="bg-green-500">Exzellent für Voice Cloning</Badge>
    } else if (transcription_suitable) {
      return <Badge variant="secondary">Gut für Transkription</Badge>
    } else {
      return <Badge variant="destructive">Niedrige Qualität</Badge>
    }
  }

  const getSegmentationIcon = (type) => {
    switch (type) {
      case 'sentence':
        return <Type className="h-4 w-4" />
      case 'paragraph':
        return <AlignLeft className="h-4 w-4" />
      case 'time':
        return <Clock className="h-4 w-4" />
      default:
        return <Scissors className="h-4 w-4" />
    }
  }

  const getSegmentationLabel = (type) => {
    switch (type) {
      case 'sentence':
        return 'Satz'
      case 'paragraph':
        return 'Absatz'
      case 'time':
        return 'Zeit'
      default:
        return 'Unbekannt'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            WhatsApp Voice Processor
          </h1>
          <p className="text-lg text-gray-600">
            Professionelle Audio-Verarbeitung mit intelligenter Segmentierung, Qualitätsbewertung und Transkription
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Dateien hochladen
              </CardTitle>
              <CardDescription>
                Unterstützte Formate: MP3, WAV, OPUS, OGG, FLAC, M4A, AAC, WMA
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <FileAudio className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">
                  Dateien hier ablegen oder klicken zum Auswählen
                </p>
                <input
                  type="file"
                  multiple
                  accept="audio/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload">
                  <Button variant="outline" className="cursor-pointer">
                    Dateien auswählen
                  </Button>
                </label>
              </div>

              {/* Segmentation Options */}
              <div className="mt-6">
                <Label className="text-base font-medium mb-3 block">Segmentierungsart wählen:</Label>
                <RadioGroup value={segmentationType} onValueChange={setSegmentationType} className="grid grid-cols-1 gap-3">
                  <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50">
                    <RadioGroupItem value="sentence" id="sentence" />
                    <Label htmlFor="sentence" className="flex items-center gap-2 cursor-pointer flex-1">
                      <Type className="h-4 w-4" />
                      <div>
                        <div className="font-medium">Sätze</div>
                        <div className="text-sm text-gray-500">Segmentierung nach einzelnen Sätzen (empfohlen)</div>
                      </div>
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50">
                    <RadioGroupItem value="paragraph" id="paragraph" />
                    <Label htmlFor="paragraph" className="flex items-center gap-2 cursor-pointer flex-1">
                      <AlignLeft className="h-4 w-4" />
                      <div>
                        <div className="font-medium">Absätze</div>
                        <div className="text-sm text-gray-500">Gruppierung von Sätzen basierend auf Pausen</div>
                      </div>
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50">
                    <RadioGroupItem value="time" id="time" />
                    <Label htmlFor="time" className="flex items-center gap-2 cursor-pointer flex-1">
                      <Clock className="h-4 w-4" />
                      <div>
                        <div className="font-medium">Zeitbasiert</div>
                        <div className="text-sm text-gray-500">Feste 30-Sekunden-Segmente</div>
                      </div>
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              {files.length > 0 && (
                <div className="mt-4">
                  <h3 className="font-medium mb-2">Ausgewählte Dateien ({files.length})</h3>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {files.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                        <span className="text-sm truncate">{file.name}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(index)}
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-4 space-y-2">
                <Button 
                  onClick={processFiles} 
                  disabled={files.length === 0 || processing}
                  className="w-full"
                >
                  {processing ? 'Verarbeitung läuft...' : 'Dateien verarbeiten'}
                </Button>
                
                {processing && (
                  <div className="space-y-2">
                    <Progress value={uploadProgress} className="w-full" />
                    <p className="text-sm text-gray-600 text-center">
                      Upload: {uploadProgress}%
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Statistics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Verarbeitungsstatistiken
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{files.length}</div>
                  <div className="text-sm text-gray-600">Dateien ausgewählt</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {results.filter(r => r.status === 'success').length}
                  </div>
                  <div className="text-sm text-gray-600">Erfolgreich verarbeitet</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {results.filter(r => r.quality_assessment?.transcription_suitable).length}
                  </div>
                  <div className="text-sm text-gray-600">Transkription geeignet</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {results.filter(r => r.quality_assessment?.voice_cloning_suitable).length}
                  </div>
                  <div className="text-sm text-gray-600">Voice Cloning geeignet</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results Section */}
        {results.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Verarbeitungsergebnisse
                </CardTitle>
                <Button onClick={downloadCSV} variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  CSV für TTS Kokei herunterladen
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {results.map((result, index) => (
                  <Card key={index} className="border-l-4 border-l-blue-500">
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(result.status)}
                          <h3 className="font-medium">{result.original_filename}</h3>
                        </div>
                        {result.quality_assessment && getQualityBadge(result.quality_assessment)}
                      </div>

                      {result.status === 'error' && (
                        <Alert variant="destructive" className="mb-3">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>{result.error}</AlertDescription>
                        </Alert>
                      )}

                      {result.status === 'success' && (
                        <Tabs defaultValue="transcription" className="w-full">
                          <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="transcription">Transkription</TabsTrigger>
                            <TabsTrigger value="quality">Qualität</TabsTrigger>
                            <TabsTrigger value="segments">Segmente</TabsTrigger>
                          </TabsList>
                          
                          <TabsContent value="transcription" className="mt-4">
                            {result.transcription ? (
                              <div className="space-y-2">
                                <div className="bg-gray-50 p-3 rounded">
                                  <p className="text-sm font-medium mb-1">Vollständige Transkription:</p>
                                  <p className="text-sm">{result.transcription.text}</p>
                                </div>
                                <div className="text-xs text-gray-500">
                                  Sprache: {result.transcription.language}
                                </div>
                              </div>
                            ) : (
                              <p className="text-sm text-gray-500">Keine Transkription verfügbar</p>
                            )}
                          </TabsContent>
                          
                          <TabsContent value="quality" className="mt-4">
                            {result.quality_assessment && (
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm font-medium">Qualitätsscore</p>
                                  <div className="flex items-center gap-2
(Content truncated due to size limit. Use page ranges or line ranges to read remaining content)