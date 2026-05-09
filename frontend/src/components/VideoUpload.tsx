import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function VideoUpload({ onFile, disabled }: Props) {
  const onDrop = useCallback((files: File[]) => {
    if (files[0]) onFile(files[0]);
  }, [onFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.mov', '.avi'] },
    maxFiles: 1,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      style={{
        border: '2px dashed #555',
        borderRadius: 8,
        padding: 40,
        textAlign: 'center',
        cursor: disabled ? 'not-allowed' : 'pointer',
        background: isDragActive ? '#222' : '#111',
        color: '#ccc',
      }}
    >
      <input {...getInputProps()} />
      {isDragActive
        ? 'Drop video here...'
        : 'Drag & drop a video (MP4, MOV, AVI) or click to select'}
    </div>
  );
}
