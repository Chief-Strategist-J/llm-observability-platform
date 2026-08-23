import { CentralMessagingTracer } from '@observability/core';

export class MessagingTracer {
  public static createProducerSpan(topic: string, eventName: string, headers?: any) {
    return CentralMessagingTracer.createProducerSpan(topic, eventName, headers, 'auth-service');
  }

  public static createConsumerSpan(event: any, topic: string) {
    return CentralMessagingTracer.createConsumerSpan(event, topic, 'auth-service');
  }

  public static finishSpan(span: any, error?: Error) {
    return CentralMessagingTracer.finishSpan(span, error);
  }
}
