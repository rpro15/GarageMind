"""initial_schema

Revision ID: 06b40454b9fe
Revises: 
Create Date: 2026-07-09 15:25:19.282459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06b40454b9fe'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание начальной схемы базы знаний GarageMind."""
    
    # Таблица моделей автомобилей
    op.create_table(
        'car_models',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('year_start', sa.Integer(), default=2000),
        sa.Column('year_end', sa.Integer(), default=2026),
        sa.Column('tire_sizes', sa.String(), default=''),
        sa.Column('wheel_pcd', sa.String(), default=''),
        sa.Column('wheel_et', sa.String(), default=''),
        sa.Column('wheel_dia', sa.String(), default=''),
        sa.Column('bolt_thread', sa.String(), default=''),
        sa.Column('bolt_type', sa.String(), default='bolt'),
        sa.Column('popular_tires', sa.String(), default=''),
        sa.UniqueConstraint('brand', 'model', 'year_start', 'year_end')
    )
    op.create_index('idx_car_models_brand', 'car_models', ['brand'])
    op.create_index('idx_car_models_model', 'car_models', ['model'])

    # Таблица отзывов
    op.create_table(
        'tire_reviews',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('car_id', sa.Integer(), nullable=False),
        sa.Column('tire_name', sa.String(), nullable=False),
        sa.Column('tire_size', sa.String(), default=''),
        sa.Column('rating', sa.Float(), default=0.0),
        sa.Column('pros', sa.String(), default=''),
        sa.Column('cons', sa.String(), default=''),
        sa.Column('text', sa.String(), default=''),
        sa.Column('source', sa.String(), default=''),
        sa.Column('date_added', sa.String(), default=''),
        sa.Column('helpful_count', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['car_id'], ['car_models.id'])
    )
    op.create_index('idx_tire_reviews_car_id', 'tire_reviews', ['car_id'])
    op.create_index('idx_tire_reviews_tire_name', 'tire_reviews', ['tire_name'])

    # Таблица известных проблем
    op.create_table(
        'tire_problems',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('car_id', sa.Integer(), nullable=False),
        sa.Column('tire_name', sa.String(), nullable=False),
        sa.Column('problem', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), default='warning'),
        sa.Column('source', sa.String(), default=''),
        sa.ForeignKeyConstraint(['car_id'], ['car_models.id'])
    )
    op.create_index('idx_tire_problems_car_id', 'tire_problems', ['car_id'])

    # Таблица характеристик шин
    op.create_table(
        'tire_specs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('category', sa.String(), default=''),
        sa.Column('size', sa.String(), default=''),
        sa.Column('load_index', sa.String(), default=''),
        sa.Column('speed_index', sa.String(), default=''),
        sa.Column('noise_db', sa.Float(), default=0.0),
        sa.Column('fuel_class', sa.String(), default=''),
        sa.Column('wet_grip', sa.String(), default=''),
        sa.Column('tread_depth', sa.Float(), default=0.0),
        sa.Column('runflat', sa.Integer(), default=0),
        sa.Column('ev_compatible', sa.Integer(), default=0)
    )
    op.create_index('idx_tire_specs_category', 'tire_specs', ['category'])

    # Таблицы персонализации (из user_history.py)
    op.create_table(
        'user_profiles',
        sa.Column('user_id', sa.String(), primary_key=True),
        sa.Column('first_seen', sa.String(), default=''),
        sa.Column('last_seen', sa.String(), default=''),
        sa.Column('total_queries', sa.Integer(), default=0),
        sa.Column('preferred_brand', sa.String(), default=''),
        sa.Column('preferred_model', sa.String(), default=''),
        sa.Column('preferred_driving_style', sa.String(), default='comfort'),
        sa.Column('preferred_season', sa.String(), default=''),
        sa.Column('preferred_budget', sa.Integer(), nullable=True)
    )

    op.create_table(
        'user_queries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('brand', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('driving_style', sa.String(), nullable=True),
        sa.Column('season', sa.String(), nullable=True),
        sa.Column('budget', sa.Integer(), nullable=True),
        sa.Column('queried_at', sa.String(), default=''),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.user_id'])
    )
    op.create_index('idx_user_queries_user_id', 'user_queries', ['user_id'])

    op.create_table(
        'user_purchases',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('tire_name', sa.String(), nullable=False),
        sa.Column('purchased_at', sa.String(), default=''),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.user_id'])
    )
    op.create_index('idx_user_purchases_user_id', 'user_purchases', ['user_id'])


def downgrade() -> None:
    """Откат всех таблиц."""
    op.drop_table('user_purchases')
    op.drop_table('user_queries')
    op.drop_table('user_profiles')
    op.drop_table('tire_specs')
    op.drop_table('tire_problems')
    op.drop_table('tire_reviews')
    op.drop_table('car_models')
