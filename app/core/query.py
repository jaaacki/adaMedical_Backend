# app/core/query.py
from flask import request
from sqlalchemy import desc, asc

class QueryBuilder:
    """Query builder for list endpoints with filtering, sorting, and pagination."""
    
    def __init__(self, model_class, default_page_size=20):
        self.model_class = model_class
        self.default_page_size = default_page_size
        self.query = model_class.query
    
    def filter_by(self, **kwargs):
        """Apply equal filters."""
        for field, value in kwargs.items():
            if hasattr(self.model_class, field) and value is not None:
                self.query = self.query.filter(getattr(self.model_class, field) == value)
        return self
    
    def search(self, search_term, fields):
        """Search in specified fields."""
        if search_term and fields:
            conditions = []
            for field in fields:
                if hasattr(self.model_class, field):
                    conditions.append(getattr(self.model_class, field).ilike(f'%{search_term}%'))
            if conditions:
                from sqlalchemy import or_
                self.query = self.query.filter(or_(*conditions))
        return self
    
    def apply_request_filters(self, exclude=None):
        """Apply filters from request args."""
        exclude = exclude or []
        for key, value in request.args.items():
            if key not in exclude and hasattr(self.model_class, key):
                self.query = self.query.filter(getattr(self.model_class, key) == value)
        return self
    
    def sort(self, sort_by=None, sort_dir=None):
        """Apply sorting."""
        sort_by = sort_by or request.args.get('sort_by', 'id')
        sort_dir = sort_dir or request.args.get('sort_dir', 'asc')
        
        if hasattr(self.model_class, sort_by):
            field = getattr(self.model_class, sort_by)
            if sort_dir.lower() == 'desc':
                self.query = self.query.order_by(desc(field))
            else:
                self.query = self.query.order_by(asc(field))
        return self
    
    def paginate(self, page=None, page_size=None):
        """Apply pagination."""
        page = page or int(request.args.get('page', 1))
        page_size = page_size or int(request.args.get('page_size', self.default_page_size))
        
        pagination = self.query.paginate(page=page, per_page=page_size, error_out=False)
        return {
            'items': pagination.items,
            'pagination': {
                'page': pagination.page,
                'page_size': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total
            }
        }
    
    def all(self):
        """Execute query and return all results."""
        return self.query.all()
    
    def first(self):
        """Execute query and return first result."""
        return self.query.first()