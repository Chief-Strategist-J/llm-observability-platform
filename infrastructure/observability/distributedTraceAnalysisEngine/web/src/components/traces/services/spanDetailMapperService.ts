import { Span } from '../../../types/trace';
import { IFormattingService } from './formattingService';

// Span detail mapper service interface (Port)
export interface ISpanDetailMapperService {
  mapSpanToDetailRows(span: Span, formattingService: IFormattingService): [string, string][];
}

// Span detail mapper service implementation
export class SpanDetailMapperService implements ISpanDetailMapperService {
  mapSpanToDetailRows(span: Span, formattingService: IFormattingService): [string, string][] {
    return [
      ['span_id', span.span_id],
      ['parent', (span.parent_span_id as string) ?? '—'],
      ['service', span.service_name],
      ['operation', span.operation_name],
      ['duration', formattingService.formatDuration(span.duration_ns)],
      ['status', 'OK'],
      ['trace_id', '—']
    ];
  }
}
