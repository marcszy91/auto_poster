import React, { useCallback, useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface ImageUploadProps {
  onMainImageChange: (file: File | null) => void;
  onAdditionalImagesChange: (files: File[]) => void;
  mainImage: File | null;
  additionalImages: File[];
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
  onMainImageChange,
  onAdditionalImagesChange,
  mainImage,
  additionalImages,
}) => {
  const [mainImagePreview, setMainImagePreview] = useState<string | null>(null);
  const [additionalPreviews, setAdditionalPreviews] = useState<string[]>([]);

  useEffect(() => {
    if (!mainImage) {
      setMainImagePreview(null);
    } else if (mainImage instanceof File) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setMainImagePreview(reader.result as string);
      };
      reader.readAsDataURL(mainImage);
    }
  }, [mainImage]);

  const onMainDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        onMainImageChange(file);
      }
    },
    [onMainImageChange]
  );

  const onAdditionalDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles = [...additionalImages, ...acceptedFiles];
      onAdditionalImagesChange(newFiles);

      // Create previews
      const previews = newFiles.map((file) => {
        return new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => {
            resolve(reader.result as string);
          };
          reader.readAsDataURL(file);
        });
      });

      Promise.all(previews).then(setAdditionalPreviews);
    },
    [additionalImages, onAdditionalImagesChange]
  );

  const removeMainImage = () => {
    onMainImageChange(null);
  };

  const removeAdditionalImage = (index: number) => {
    const newFiles = additionalImages.filter((_, i) => i !== index);
    const newPreviews = additionalPreviews.filter((_, i) => i !== index);
    onAdditionalImagesChange(newFiles);
    setAdditionalPreviews(newPreviews);
  };

  const mainDropzone = useDropzone({
    onDrop: onMainDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
    },
    maxFiles: 1,
    multiple: false,
  });

  const additionalDropzone = useDropzone({
    onDrop: onAdditionalDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
    },
    multiple: true,
  });

  return (
    <div className="space-y-6">
      {/* Main Image Upload */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Main Image <span className="text-red-500">*</span>
        </label>
        {!mainImagePreview ? (
          <div
            {...mainDropzone.getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              mainDropzone.isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-primary-400'
            }`}
          >
            <input {...mainDropzone.getInputProps()} />
            <div className="space-y-2">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
                aria-hidden="true"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="text-sm text-gray-600">
                <span className="text-primary-600 font-medium">Click to upload</span> or drag and
                drop
              </div>
              <p className="text-xs text-gray-500">PNG, JPG, JPEG or WEBP (Max 10MB)</p>
            </div>
          </div>
        ) : (
          <div className="relative inline-block">
            <img
              src={mainImagePreview}
              alt="Main preview"
              className="w-full max-w-md h-auto rounded-lg shadow-md"
            />
            <button
              type="button"
              onClick={removeMainImage}
              className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-2 hover:bg-red-600 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Additional Images Upload */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Additional Images (Optional)
        </label>
        <div
          {...additionalDropzone.getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            additionalDropzone.isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400'
          }`}
        >
          <input {...additionalDropzone.getInputProps()} />
          <p className="text-sm text-gray-600">
            <span className="text-primary-600 font-medium">Click to upload</span> or drag and drop
            additional images
          </p>
        </div>

        {/* Additional Images Preview */}
        {additionalPreviews.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
            {additionalPreviews.map((preview, index) => (
              <div key={index} className="relative group">
                <img
                  src={preview}
                  alt={`Additional preview ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg shadow-sm"
                />
                <button
                  type="button"
                  onClick={() => removeAdditionalImage(index)}
                  className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
