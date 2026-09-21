"""Offline plumbing baseline, not a competitive classifier."""
def create():
    return lambda request: {'label': 'noise'}
