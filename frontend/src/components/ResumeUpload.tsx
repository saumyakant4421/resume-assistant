import { useState } from "react";
import { Upload } from "lucide-react";
import { useDropzone } from "react-dropzone";

interface ResumeUploadProps {
  onUpload: (file: File) => void;
  isLoading?: boolean;
}

export default function ResumeUpload({ onUpload, isLoading }: ResumeUploadProps) {
  const [fileName, setFileName] = useState<string | null>(null);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
    },
    onDrop: (files) => {
      if (files[0]) {
        setFileName(files[0].name);
        onUpload(files[0]);
      }
    },
    disabled: isLoading,
  });

  return (
    <div className="app-upload">
      <div className="app-upload__header">
        <div className="app-upload__icon">
          <Upload size={18} />
        </div>
        <div>
          <p className="app-upload__eyebrow">Upload intake</p>
          <h3 className="app-upload__title">Upload Resume</h3>
          <p className="app-upload__copy">Drag and drop a PDF or TXT file, or choose one from your computer.</p>
        </div>
      </div>

      <div
        {...getRootProps()}
        className={`app-upload__dropzone ${isDragActive ? "app-upload__dropzone--active" : "app-upload__dropzone--idle"} ${isLoading ? "app-upload__dropzone--loading" : ""}`}
      >
        <input {...getInputProps()} />
        <p className="app-upload__dropzone-title">{isDragActive ? "Drop the resume here" : "Drop file here or click to browse"}</p>
        <p className="app-upload__dropzone-copy">PDF or TXT files accepted</p>

        {fileName && <div className="app-upload__file-pill">✓ {fileName} uploaded</div>}
      </div>
    </div>
  );
}
