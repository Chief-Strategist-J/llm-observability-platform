export interface KafkaTopicSpec {
  name: string;
  numPartitions: number;
  replicationFactor: number;
  configEntries: {
    'retention.ms'?: string;
    'cleanup.policy'?: 'delete' | 'compact' | 'delete,compact';
    'min.insync.replicas'?: string;
    'segment.bytes'?: string;
  };
}

export interface TopicMigrationResult {
  topic: string;
  status: 'created' | 'updated' | 'already_exists' | 'rolled_back' | 'failed';
  details?: string;
}

export class KafkaTopicProvisioner {
  private provisionedTopics: Map<string, KafkaTopicSpec> = new Map();

  public async applyMigration(spec: KafkaTopicSpec): Promise<TopicMigrationResult> {
    if (this.provisionedTopics.has(spec.name)) {
      return {
        topic: spec.name,
        status: 'already_exists',
        details: `Topic ${spec.name} is already provisioned with ${spec.numPartitions} partitions`,
      };
    }

    this.provisionedTopics.set(spec.name, spec);
    console.log(
      `[KafkaTopicProvisioner] Provisioned Topic '${spec.name}' [Partitions: ${spec.numPartitions}, RepFactor: ${spec.replicationFactor}]`,
    );

    return {
      topic: spec.name,
      status: 'created',
    };
  }

  public async rollbackMigration(topicName: string): Promise<TopicMigrationResult> {
    if (this.provisionedTopics.has(topicName)) {
      this.provisionedTopics.delete(topicName);
      console.log(`[KafkaTopicProvisioner] Rolled back Topic '${topicName}'`);
      return {
        topic: topicName,
        status: 'rolled_back',
      };
    }

    return {
      topic: topicName,
      status: 'failed',
      details: `Topic ${topicName} was not found in provisioner state`,
    };
  }
}
