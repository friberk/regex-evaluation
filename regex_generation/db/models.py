import uuid
import datetime
from peewee import (
    BooleanField, Model, TextField, BlobField, IntegerField, DateTimeField, FloatField,
    ForeignKeyField, DecimalField, CharField, Check, DatabaseProxy
)
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField

db_proxy = DatabaseProxy()

class BaseModel(Model):
    class Meta:
        database = db_proxy

# =============================================
# reuse_by_example_generation_tasks
# =============================================
class RbeGenerationTask(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    ground_truth = TextField(null=True)
    positive_examples = JSONField()   # stored as TEXT, queried with JSON1
    negative_examples = JSONField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "rbe_generation_tasks"
    # UNIQUE(ground_truth, positive_examples, negative_examples)
    indexes = (
        (('ground_truth', 'positive_examples', 'negative_examples'), True),
    )

# =============================================
# reuse_by_example_generation_queries
# =============================================
class RbeGenerationQuery(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    task = ForeignKeyField(
        RbeGenerationTask,
        backref='queries',
        on_delete='CASCADE',
        to_field='id',
        column_name='task_id'
    )
    query_parameters = JSONField(null=True)
    status = CharField(
        max_length=16,
        constraints=[Check('status IN ("success","error","pending","solution_not_found","not_satisfied","timeout")')]
    )
    error_message = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "rbe_generation_queries"

# =============================================
# reuse_by_example_generated_candidates
# =============================================
class RbeGeneratedCandidate(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    query = ForeignKeyField(
        RbeGenerationQuery,
        backref='candidates',
        on_delete='CASCADE',
        to_field='id',
        column_name='query_id'
    )
    regex_pattern = TextField()
    accuracy = DecimalField(max_digits=5, decimal_places=4, null=True)
    syntactic_similarity = DecimalField(max_digits=5, decimal_places=4, null=True)
    semantic_similarity = DecimalField(max_digits=5, decimal_places=4, null=True)
    strictness_score = DecimalField(max_digits=5, decimal_places=4, null=True)
    generation_time = FloatField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "rbe_generated_candidates"

# =============================================
# llm_generation_tasks
# =============================================
class LlmGenerationTask(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    ground_truth = TextField(null=True)
    positive_examples = JSONField()   # stored as TEXT, queried with JSON1
    negative_examples = JSONField()
    # store UTC; SQLite has no TZ-aware type
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "llm_generation_tasks"
        # UNIQUE(ground_truth, positive_examples, negative_examples)
        indexes = (
            (('ground_truth', 'positive_examples', 'negative_examples'), True),
        )

# =============================================
# llm_generation_queries
# =============================================
class LlmGenerationQuery(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    task = ForeignKeyField(
        LlmGenerationTask,
        backref='queries',
        on_delete='CASCADE',
        to_field='id',
        column_name='task_id'
    )
    query_parameters = JSONField(null=True)
    system_prompt = TextField(null=True)
    status = CharField(
        max_length=16,
        constraints=[Check('status IN ("success","error","pending","retry_exceeded")')]
    )
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "llm_generation_queries"

# =============================================
# llm_generation_attempts
# =============================================
class LlmGenerationAttempt(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    query = ForeignKeyField(
        LlmGenerationQuery,
        backref='attempts',
        on_delete='CASCADE',
        to_field='id',
        column_name='query_id'
    )
    request_payload = JSONField(null=True)
    attempt_number = IntegerField()
    status = CharField(
        max_length=16,
        constraints=[Check('status IN ("success","error","pending","not_satisfied","timeout")')]
    )
    response_payload = JSONField(null=True)
    error_message = TextField(null=True)
    response_received_at = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "llm_generation_attempts"
        indexes = (
            (('query', 'attempt_number'), True),  # UNIQUE(query_id, attempt_number)
        )

# =============================================
# llm_generated_candidates
# =============================================
class LlmGeneratedCandidate(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    query = ForeignKeyField(
        LlmGenerationQuery,
        backref='candidates',
        on_delete='CASCADE',
        to_field='id',
        column_name='query_id'
    )
    attempt = ForeignKeyField(
        LlmGenerationAttempt,
        backref='candidates',
        on_delete='CASCADE',
        to_field='id',
        column_name='attempt_id'
    )
    regex_pattern = TextField()
    accuracy = DecimalField(max_digits=5, decimal_places=4, null=True)
    syntactic_similarity = DecimalField(max_digits=5, decimal_places=4, null=True)
    semantic_similarity = DecimalField(max_digits=5, decimal_places=4, null=True)
    strictness_score = DecimalField(max_digits=5, decimal_places=4, null=True)
    # llm_type = CharField(
    #     max_length=1, null=True,
    #     constraints=[Check('llm_type IN ("L","C","B")')]
    # )
    generation_time = FloatField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "llm_generated_candidates"

# =============================================
# synthesizer_generation_tasks
# =============================================
class SynthesizerGenerationTask(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    ground_truth = TextField(null=True)
    positive_examples = JSONField()   # stored as TEXT, queried with JSON1
    negative_examples = JSONField()
    # store UTC; SQLite has no TZ-aware type
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "synthesizer_generation_tasks"
        # UNIQUE(ground_truth, positive_examples, negative_examples)
        indexes = (
            (('ground_truth', 'positive_examples', 'negative_examples'), True),
        )

# =============================================
# synthesizer_generation_queries
# =============================================
class SynthesizerGenerationQuery(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    task = ForeignKeyField(
        SynthesizerGenerationTask,
        backref='queries',
        on_delete='CASCADE',
        to_field='id',
        column_name='task_id'
    )
    query_parameters = JSONField(null=True)
    status = CharField(
        max_length=16,
        constraints=[Check('status IN ("success","error","pending","not_satisfied","solution_not_found","timeout")')]
    )
    error_message = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "synthesizer_generation_queries"

# =============================================
# synthesizer_generated_candidates
# =============================================
class SynthesizerGeneratedCandidate(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    query = ForeignKeyField(
        SynthesizerGenerationQuery,
        backref='candidates',
        on_delete='CASCADE',
        to_field='id',
        column_name='query_id'
    )
    regex_pattern = TextField()
    accuracy = DecimalField(max_digits=5, decimal_places=4, null=True)
    syntactic_similarity = DecimalField(max_digits=5, decimal_places=4, null=True)
    semantic_similarity = DecimalField(max_digits=5, decimal_places=4, null=True)
    strictness_score = DecimalField(max_digits=5, decimal_places=4, null=True)
    generation_time = FloatField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "synthesizer_generated_candidates"

# =============================================
# candidate_regex_metrics
# =============================================
class CandidateRegexMetric(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    rbe_candidate = ForeignKeyField(
        RbeGeneratedCandidate,
        backref='metrics',
        null=True,
        on_delete='CASCADE',
        to_field='id',
        column_name='rbe_candidate_id'
    )
    llm_candidate = ForeignKeyField(
        LlmGeneratedCandidate,
        backref='metrics',
        null=True,
        on_delete='CASCADE',
        to_field='id',
        column_name='llm_candidate_id'
    )
    synthesizer_candidate = ForeignKeyField(
        SynthesizerGeneratedCandidate,
        backref='metrics',
        null=True,
        on_delete='CASCADE',
        to_field='id',
        column_name='synthesizer_candidate_id'
    )
    pattern_length = IntegerField(null=True)
    ground_truth_pattern_length = IntegerField(null=True)
    ground_truth_distinct_features = IntegerField(null=True)
    distinct_features = IntegerField(null=True)
    syntactic_similarity = JSONField(null=True)
    automaton_size = JSONField(null=True)
    strictness_score = JSONField(null=True)
    semantic_similarity = JSONField(null=True)

    class Meta:
        table_name = "candidate_regex_metrics"
        constraints = [
            # Exactly one of the three is non-NULL.
            Check('((rbe_candidate_id IS NOT NULL) + (llm_candidate_id IS NOT NULL) + (synthesizer_candidate_id IS NOT NULL)) = 1')
        ]
        # UNIQUE(rbe_candidate_id, llm_candidate_id, synthesizer_candidate_id)
        indexes = (
            (('rbe_candidate_id', 'llm_candidate_id', 'synthesizer_candidate_id'), True),
        )

    @property
    def candidate(self):
        return self.rbe_candidate or self.llm_candidate or self.synthesizer_candidate

    def set_candidate(self, obj):
        if isinstance(obj, RbeGeneratedCandidate):
            self.rbe_candidate, self.llm_candidate, self.synthesizer_candidate = obj, None, None
        elif isinstance(obj, LlmGeneratedCandidate):
            self.llm_candidate, self.rbe_candidate, self.synthesizer_candidate = obj, None, None
        elif isinstance(obj, SynthesizerGeneratedCandidate):
            self.synthesizer_candidate, self.rbe_candidate, self.llm_candidate = obj, None, None
        else:
            raise ValueError("Unsupported candidate type")


# =============================================
# ground_truth_metrics
# =============================================
class GroundTruthMetric(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    ground_truth = TextField()
    positive_examples = JSONField()
    negative_examples = JSONField()
    pattern_length = IntegerField(null=True)
    distinct_features = IntegerField(null=True)
    automaton_size = JSONField(null=True)
    strictness_score = JSONField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "ground_truth_metrics"
        # UNIQUE(ground_truth, positive_examples, negative_examples)
        indexes = (
            (('ground_truth', 'positive_examples', 'negative_examples'), True),
        )

class StrictnessScore(BaseModel):
    id = CharField(primary_key=True, max_length=36, default=lambda: str(uuid.uuid4()))
    # Either of these can be set, but not both.
    rbe_candidate = ForeignKeyField(
        RbeGeneratedCandidate,
        null=True, backref='strictness_scores',
        on_delete='CASCADE', to_field='id',
        column_name='rbe_candidate_id'
    )
    llm_candidate = ForeignKeyField(
        LlmGeneratedCandidate,
        null=True, backref='strictness_scores',
        on_delete='CASCADE', to_field='id',
        column_name='llm_candidate_id'
    )

    strictness_score = DecimalField(max_digits=5, decimal_places=4, null=True)
    aligned_edges = IntegerField(null=True)
    candidate_edges = IntegerField(null=True)
    adapted_candidate_regex = TextField(null=True)
    status = CharField(
        max_length=16,
        constraints=[Check('status IN ("success","timeout","error")')]
    )
    error_message = TextField(null=True)
    time_taken = FloatField(null=True)
    approximate = BooleanField(null=True)
    restrict_alphabet = BooleanField(null=True)
    gamma = FloatField(null=True)
    mode = CharField(max_length=16, null=True)
    symbolic_automata = BooleanField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "strictness_scores"
        constraints = [
            # Exactly one of the two is non-NULL (XOR).
            Check('(rbe_candidate_id IS NULL) <> (llm_candidate_id IS NULL)')
        ]

    @property
    def candidate(self):
        return self.rbe_candidate or self.llm_candidate

    def set_candidate(self, obj):
        if isinstance(obj, RbeGeneratedCandidate):
            self.rbe_candidate, self.llm_candidate = obj, None
        elif isinstance(obj, LlmGeneratedCandidate):
            self.llm_candidate, self.rbe_candidate = obj, None
        else:
            raise ValueError("Unsupported candidate type")