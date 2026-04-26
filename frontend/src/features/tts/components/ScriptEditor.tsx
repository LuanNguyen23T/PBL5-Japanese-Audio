import React, { useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Textarea } from '@/components/ui/textarea';
import { FileText } from 'lucide-react';

interface ScriptEditorProps {
  title?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  minHeight?: string;
}

export const ScriptEditor: React.FC<ScriptEditorProps> = ({ 
  title = "Kịch bản hội thoại", 
  placeholder = "Nhập kịch bản ở đây...\nVí dụ:\n男: こんにちは、元気ですか？\n女: はい、元気です。", 
  value, 
  onChange,
  minHeight = "min-h-[300px]"
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  return (
    <Card className="shadow-lg border-2 border-blue-100 dark:border-blue-900/40">
      <CardHeader className="bg-gradient-to-r from-blue-50/50 to-indigo-50/50 dark:from-blue-900/20 dark:to-indigo-900/20 border-b pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <CardTitle className="flex items-center gap-2 text-blue-700 dark:text-blue-400 text-lg">
            <FileText className="w-5 h-5" />
            {title}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Textarea
          ref={textareaRef}
          className={`${minHeight} w-full resize-y border-0 focus-visible:ring-0 rounded-none p-6 text-base leading-relaxed bg-transparent`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
      </CardContent>
    </Card>
  );
};
