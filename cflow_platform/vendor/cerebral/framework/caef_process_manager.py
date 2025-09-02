#!/usr/bin/env python3
"""
CAEF Process Manager - Clean Multiprocessing Resource Management
==============================================================
Date: December 23, 2025
System: CAEF Research Enhancement
Authority: AEMI - Atomic Enterprise Methodology Implementation

Handles proper cleanup of multiprocessing resources to prevent semaphore leaks.
"""

import atexit
import logging
import multiprocessing
import threading
import time
import weakref
from typing import List, Set
import concurrent.futures

logger = logging.getLogger(__name__)


class CAEFProcessManager:
    """
    Enterprise-grade process manager for CAEF operations
    
    Features:
    - Automatic semaphore cleanup
    - Process pool management
    - Resource leak prevention
    - Graceful shutdown handling
    """
    
    def __init__(self):
        """Initialize process manager with cleanup tracking"""
        self.active_pools: Set[concurrent.futures.ProcessPoolExecutor] = set()
        self.active_processes: Set[multiprocessing.Process] = set()
        self.cleanup_registered = False
        
        # Track resources using weak references to avoid circular refs
        self._tracked_resources = weakref.WeakSet()
        
        # Register cleanup on exit
        self._register_cleanup()
        
        logger.info("CAEF Process Manager initialized with resource tracking")
    
    def _register_cleanup(self):
        """Register cleanup handlers"""
        if not self.cleanup_registered:
            atexit.register(self.cleanup_all_resources)
            self.cleanup_registered = True
            logger.info("Process cleanup handlers registered")
    
    def create_process_pool(self, max_workers: int = None) -> concurrent.futures.ProcessPoolExecutor:
        """Create a managed process pool"""
        if max_workers is None:
            max_workers = min(4, multiprocessing.cpu_count())
        
        pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=max_workers,
            mp_context=multiprocessing.get_context('spawn')  # Use spawn for cleaner resource management
        )
        
        # Track the pool for cleanup
        self.active_pools.add(pool)
        self._tracked_resources.add(pool)
        
        logger.info(f"Created process pool with {max_workers} workers")
        return pool
    
    def shutdown_pool(self, pool: concurrent.futures.ProcessPoolExecutor, wait: bool = True, timeout: float = 30.0):
        """Safely shutdown a process pool"""
        try:
            if pool in self.active_pools:
                logger.info("Shutting down process pool...")
                pool.shutdown(wait=wait, timeout=timeout)
                self.active_pools.discard(pool)
                logger.info("Process pool shutdown complete")
        except Exception as e:
            logger.warning(f"Error during pool shutdown: {e}")
    
    def create_process(self, target, args=(), kwargs=None) -> multiprocessing.Process:
        """Create a managed process"""
        if kwargs is None:
            kwargs = {}
        
        process = multiprocessing.Process(
            target=target,
            args=args,
            kwargs=kwargs
        )
        
        # Track the process for cleanup
        self.active_processes.add(process)
        self._tracked_resources.add(process)
        
        logger.info(f"Created managed process: {process.name}")
        return process
    
    def cleanup_process(self, process: multiprocessing.Process, timeout: float = 10.0):
        """Safely cleanup a process"""
        try:
            if process in self.active_processes:
                logger.info(f"Cleaning up process: {process.name}")
                
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=timeout)
                    
                    if process.is_alive():
                        logger.warning(f"Force killing process: {process.name}")
                        process.kill()
                        process.join(timeout=5.0)
                
                self.active_processes.discard(process)
                logger.info(f"Process cleanup complete: {process.name}")
        except Exception as e:
            logger.warning(f"Error during process cleanup: {e}")
    
    def cleanup_all_resources(self):
        """Clean up all tracked resources"""
        logger.info("Starting comprehensive resource cleanup...")
        
        # Shutdown all active pools
        for pool in list(self.active_pools):
            self.shutdown_pool(pool, wait=False, timeout=10.0)
        
        # Cleanup all active processes
        for process in list(self.active_processes):
            self.cleanup_process(process, timeout=5.0)
        
        # Force cleanup any remaining multiprocessing resources
        try:
            # Get all active children and clean them up
            for child in multiprocessing.active_children():
                try:
                    if child.is_alive():
                        child.terminate()
                        child.join(timeout=2.0)
                        if child.is_alive():
                            child.kill()
                except Exception as e:
                    logger.warning(f"Error cleaning up child process: {e}")
            
            logger.info("Resource cleanup completed")
        except Exception as e:
            logger.error(f"Error during comprehensive cleanup: {e}")
    
    def get_resource_stats(self) -> dict:
        """Get current resource usage statistics"""
        return {
            "active_pools": len(self.active_pools),
            "active_processes": len(self.active_processes),
            "tracked_resources": len(self._tracked_resources),
            "system_cpu_count": multiprocessing.cpu_count(),
            "active_children": len(multiprocessing.active_children())
        }


# Global instance for process management
_process_manager = None

def get_process_manager() -> CAEFProcessManager:
    """Get or create the global process manager instance"""
    global _process_manager
    if _process_manager is None:
        _process_manager = CAEFProcessManager()
    return _process_manager


def cleanup_on_exit():
    """Cleanup function to be called on program exit"""
    global _process_manager
    if _process_manager:
        _process_manager.cleanup_all_resources()


# Ensure cleanup happens on module exit
atexit.register(cleanup_on_exit)