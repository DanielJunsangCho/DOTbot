/**
 * Main DOTbot Application
 * Coordinates AI misalignment detection workflow
 */

import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  Box,
  Typography,
  Grid,
  Alert,
  Snackbar,
  AppBar,
  Toolbar
} from '@mui/material';
import { Psychology } from '@mui/icons-material';
import { motion } from 'framer-motion';

import { UrlAnalysisForm } from './components/UrlAnalysisForm';
import { AgentVisualization } from './components/AgentVisualization';
import { ResultsDisplay } from './components/ResultsDisplay';
import { 
  getHealthStatus, 
  downloadExport,
  submitAsyncAIBehaviorAnalysis,
  getAsyncTaskStatus,
  getAsyncTaskResults
} from './api/client';
import { ScrapeRequest, WorkflowOutput, WorkflowStatus } from './types/api';

// Create MUI theme following CLAUDE.md design standards
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#667eea',
      light: '#9ca9f5',
      dark: '#3f51b5'
    },
    secondary: {
      main: '#764ba2',
      light: '#a47bcf',
      dark: '#4a2c64'
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff'
    }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700
    },
    h4: {
      fontWeight: 600
    },
    h6: {
      fontWeight: 600
    }
  },
  shape: {
    borderRadius: 12
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600
        }
      }
    }
  }
});

function App() {
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [results, setResults] = useState<WorkflowOutput | null>(null);
  const [error, setError] = useState<string>('');
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | undefined>();
  const [targetUrl, setTargetUrl] = useState<string>('');
  const [snackbarOpen, setSnackbarOpen] = useState<boolean>(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string>('');
  
  // Async task tracking
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [taskProgress, setTaskProgress] = useState<{
    progress: number;
    completed_items: number;
    total_items: number;
    status: string;
  } | null>(null);

  // Check backend health on component mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await getHealthStatus();
        console.log('Backend is healthy');
      } catch (error) {
        console.error('Backend health check failed:', error);
        showSnackbar('Warning: Unable to connect to backend service');
      }
    };
    
    checkHealth();
  }, []);


  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setSnackbarOpen(true);
  };

  const handleAnalysisSubmit = async (request: ScrapeRequest) => {
    setIsAnalyzing(true);
    setError('');
    setResults(null);
    setTargetUrl(request.url);
    setCurrentTaskId(null);
    setTaskProgress(null);

    try {
      // Submit async analysis task
      const submission = await submitAsyncAIBehaviorAnalysis(request);
      
      setCurrentTaskId(submission.task_id);
      
      setWorkflowStatus({
        status: 'running',
        start_time: new Date().toISOString(),
        current_step: 'initializing',
        step_description: 'Task submitted successfully, starting analysis...',
        url: request.url
      });

      showSnackbar(`Analysis task submitted!`);
      
      // Start polling for task progress
      startPollingTaskProgress(submission.task_id, request.url);
      
    } catch (err) {
      console.error('Task submission error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit analysis task';
      setError(errorMessage);
      setWorkflowStatus({
        status: 'failed',
        start_time: new Date().toISOString(),
        current_step: 'error',
        url: request.url,
        error: errorMessage
      });
      showSnackbar('Failed to start analysis. Please try again.');
      setIsAnalyzing(false);
    }
  };

  const startPollingTaskProgress = (taskId: string, url: string) => {
    const poll = async () => {
      try {
        const status = await getAsyncTaskStatus(taskId);
        
        if (!status) {
          throw new Error('Task not found');
        }

        // Update progress state
        setTaskProgress({
          progress: status.progress,
          completed_items: status.completed_items,
          total_items: status.total_items,
          status: status.status
        });

        // Update workflow status with real data
        const getStepFromProgress = (progress: number, taskStatus: string, completedItems: number, totalItems: number): { step: string; description: string } => {
          if (taskStatus === 'completed') {
            return { step: 'export', description: `Analysis complete! Processed ${completedItems}/${totalItems} items` };
          } else if (taskStatus === 'failed') {
            return { step: 'error', description: 'Analysis failed. Please check the logs.' };
          } else if (progress < 20) {
            return { step: 'scraping', description: `Discovering and extracting content... (${completedItems}/${totalItems} items)` };
          } else if (progress < 80) {
            return { step: 'analysis', description: `Analyzing content for AI behavior patterns... (${Math.round(progress)}% complete)` };
          } else {
            return { step: 'export', description: `Finalizing analysis results... (${Math.round(progress)}% complete)` };
          }
        };

        const stepInfo = getStepFromProgress(status.progress, status.status, status.completed_items, status.total_items);
        
        setWorkflowStatus({
          status: status.status === 'completed' ? 'completed' : 
                  status.status === 'failed' ? 'failed' : 'running',
          start_time: status.created_at,
          current_step: stepInfo.step,
          step_description: stepInfo.description,
          url: url,
          completed_time: status.completed_at,
          error: status.status === 'failed' ? 'Task failed during processing' : undefined
        });

        // Handle completion
        if (status.status === 'completed') {
          setIsAnalyzing(false);
          
          // Get final results
          const taskResults = await getAsyncTaskResults(taskId);
          if (taskResults && taskResults.results) {
            setResults(taskResults.results);
            showSnackbar(`Analysis completed! Found ${taskResults.summary.ai_reports_found} AI behavior reports from ${taskResults.summary.successful_pages} pages.`);
          } else {
            throw new Error('Could not retrieve task results');
          }
          
          return; // Stop polling
        } else if (status.status === 'failed') {
          setIsAnalyzing(false);
          setError('Analysis task failed during processing');
          showSnackbar('Analysis failed. Please try again.');
          return; // Stop polling
        }

        // Continue polling if still running
        setTimeout(poll, 3000); // Poll every 3 seconds
        
      } catch (error) {
        console.error('Polling error:', error);
        setIsAnalyzing(false);
        setError('Lost connection to analysis task');
        showSnackbar('Connection lost. Please refresh and try again.');
      }
    };

    // Start polling immediately
    poll();
  };

  const handleDownload = async (exportPath: string) => {
    try {
      const filename = exportPath.split('/').pop() || 'export';
      const exportId = filename;
      
      const blob = await downloadExport(exportId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showSnackbar('Report downloaded successfully!');
    } catch (error) {
      console.error('Download error:', error);
      showSnackbar('Failed to download report. Please try again.');
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar position="static" elevation={0} sx={{ backgroundColor: 'transparent' }}>
        <Toolbar>
          <Box display="flex" alignItems="center" flexGrow={1}>
            <Psychology sx={{ mr: 2, fontSize: 28 }} />
            <Typography variant="h6" component="div" fontWeight="bold">
              DOTbot
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <Box textAlign="center" mb={6}>
            <Typography 
              variant="h1" 
              component="h1" 
              sx={{ 
                fontSize: { xs: '2.5rem', md: '4rem', lg: '5rem' },
                fontWeight: 800,
                background: 'linear-gradient(135deg, #ffffff 0%, #e3f2fd 30%, #bbdefb 70%, #90caf9 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                color: 'transparent',
                textShadow: '0 2px 10px rgba(255,255,255,0.3), 0 4px 20px rgba(0,0,0,0.1)',
                letterSpacing: '-0.02em',
                mb: 3,
                lineHeight: 1.1,
                filter: 'drop-shadow(0 0 10px rgba(255,255,255,0.2))'
              }}
            >
              AI Misalignment Detection
            </Typography>
          </Box>
        </motion.div>

        {/* Main Content Grid */}
        <Grid container spacing={4}>
          {/* Left Column - Analysis Form */}
          <Grid item xs={12} lg={8}>
            <UrlAnalysisForm
              onSubmit={handleAnalysisSubmit}
              isLoading={isAnalyzing}
              error={error}
            />

            {/* Results Display */}
            {results && (
              <Box mt={4}>
                <ResultsDisplay 
                  results={results} 
                  onDownload={handleDownload}
                />
              </Box>
            )}
          </Grid>

          {/* Right Column - Agent Visualization */}
          <Grid item xs={12} lg={4}>
            <AgentVisualization
              workflowStatus={workflowStatus}
              isActive={isAnalyzing}
              targetUrl={targetUrl}
              taskProgress={taskProgress}
              currentTaskId={currentTaskId}
            />
          </Grid>
        </Grid>

        {/* Footer */}
        <Box mt={8} pt={4} textAlign="center" borderTop="1px solid" borderColor="divider">
          <Typography variant="body2" color="text.secondary">
            DOTbot © 2024 - AI Misalignment Detection Tool
          </Typography>
        </Box>
      </Container>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity="info"
          variant="filled"
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
}

export default App;