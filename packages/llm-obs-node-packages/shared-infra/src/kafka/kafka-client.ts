export {
  CentralizedKafkaClient,
  createKafkaClient,
  type KafkaHeaders,
  type KafkaEvent,
  type KafkaEventHandler,
} from '../infra/messaging/client-factory';

export type { KafkaBrokerConfig as KafkaConfig } from '../infra/messaging/broker-config';
