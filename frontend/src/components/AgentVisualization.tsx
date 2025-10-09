/**
 * Agent Visualization Component
 * Shows the agent's progress through website analysis
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Paper,
  Alert
} from '@mui/material';
import {
  Psychology,
  Search,
  DataObject,
  FileDownload,
  CheckCircle,
  Error,
  HourglassEmpty,
  Web
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { WorkflowStatus, AgentStep } from '../types/api';

interface AgentVisualizationProps {
  workflowStatus?: WorkflowStatus;
  isActive: boolean;
  targetUrl?: string;
  taskProgress?: {
    progress: number;
    completed_items: number;
    total_items: number;
    status: string;
  } | null;
  currentTaskId?: string | null;
}

const WORKFLOW_STEPS = [
  {
    key: 'scraping',
    label: 'Website Scraping',
    description: 'Extracting content from the target website',
    icon: <Search />
  },
  {
    key: 'processing',
    label: 'Content Processing',
    description: 'Analyzing and structuring the scraped content',
    icon: <DataObject />
  },
  {
    key: 'analysis',
    label: 'AI Behavior Analysis',
    description: 'Detecting patterns of concerning AI behavior',
    icon: <Psychology />
  },
  {
    key: 'export',
    label: 'Results Export',
    description: 'Preparing and exporting analysis results',
    icon: <FileDownload />
  }
];

export const AgentVisualization: React.FC<AgentVisualizationProps> = ({
  workflowStatus,
  isActive,
  targetUrl,
  taskProgress,
  currentTaskId
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [agentActions, setAgentActions] = useState<AgentStep[]>([]);

  useEffect(() => {
    if (!workflowStatus) return;

    const stepIndex = WORKFLOW_STEPS.findIndex(step => 
      step.key === workflowStatus.current_step
    );
    
    if (stepIndex !== -1) {
      setCurrentStepIndex(stepIndex);
    }

    // Simulate agent actions for visualization
    const newAction: AgentStep = {
      name: workflowStatus.current_step,
      description: workflowStatus.step_description || 'Processing...',
      status: workflowStatus.status === 'running' ? 'running' : 'completed',
      timestamp: new Date().toISOString(),
      details: `Working on: ${targetUrl || 'target website'}`
    };

    setAgentActions(prev => {
      const exists = prev.some(action => 
        action.name === newAction.name && action.status === newAction.status
      );
      
      if (!exists) {
        return [...prev, newAction];
      }
      
      return prev;
    });
  }, [workflowStatus, targetUrl]);

  const getStepStatus = (stepIndex: number): 'active' | 'completed' | 'disabled' => {
    if (stepIndex < currentStepIndex) return 'completed';
    if (stepIndex === currentStepIndex && isActive) return 'active';
    return 'disabled';
  };

  const getStatusColor = (status: string): 'info' | 'success' | 'error' | 'warning' => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'failed': return 'error';
      default: return 'warning';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card elevation={4} sx={{ height: 'fit-content', position: 'sticky', top: 20 }}>
        <CardContent>
          {/* Agent Header */}
          <Box display="flex" alignItems="center" mb={3}>
            <motion.div
              animate={isActive ? { rotate: 360 } : { rotate: 0 }}
              transition={{ duration: 2, repeat: isActive ? Infinity : 0, ease: "linear" }}
            >
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <Psychology />
              </Avatar>
            </motion.div>
            <Box>
              <Typography variant="h6" fontWeight="bold">
                DOTbot Agent
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {isActive ? 'Analyzing website...' : 'Ready to analyze'}
              </Typography>
            </Box>
          </Box>

          {/* Target URL Display */}
          {targetUrl && (
            <Paper variant="outlined" sx={{ p: 2, mb: 3, backgroundColor: 'grey.50' }}>
              <Box display="flex" alignItems="center">
                <Web sx={{ mr: 1, color: 'text.secondary' }} />
                <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                  <strong>Target:</strong> {targetUrl}
                </Typography>
              </Box>
            </Paper>
          )}

          {/* Status Alert */}
          {workflowStatus && (
            <Alert 
              severity={getStatusColor(workflowStatus.status)} 
              sx={{ mb: 3 }}
              variant="outlined"
            >
              <Typography variant="body2">
                <strong>Status:</strong> {workflowStatus.status.toUpperCase()}
              </Typography>
              {workflowStatus.step_description && (
                <Typography variant="caption" display="block">
                  {workflowStatus.step_description}
                </Typography>
              )}
            </Alert>
          )}

          {/* Progress Bar with Real Data */}
          {isActive && (
            <Box mb={3}>
              <LinearProgress 
                variant="determinate" 
                value={taskProgress?.progress || (currentStepIndex + 1) / WORKFLOW_STEPS.length * 100}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                {taskProgress ? 
                  `${Math.round(taskProgress.progress)}% - ${taskProgress.completed_items}/${taskProgress.total_items} items processed` :
                  `Step ${currentStepIndex + 1} of ${WORKFLOW_STEPS.length}`
                }
              </Typography>
              {currentTaskId && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Task ID: {currentTaskId}
                </Typography>
              )}
            </Box>
          )}

          {/* Workflow Steps */}
          <Stepper 
            activeStep={currentStepIndex} 
            orientation="vertical"
            sx={{ mb: 3 }}
          >
            {WORKFLOW_STEPS.map((step, index) => (
              <Step key={step.key}>
                <StepLabel 
                  icon={
                    <motion.div
                      animate={
                        getStepStatus(index) === 'active' 
                          ? { scale: [1, 1.2, 1] }
                          : { scale: 1 }
                      }
                      transition={{ 
                        duration: 1.5, 
                        repeat: getStepStatus(index) === 'active' ? Infinity : 0 
                      }}
                    >
                      {step.icon}
                    </motion.div>
                  }
                >
                  <Typography variant="subtitle2" fontWeight="medium">
                    {step.label}
                  </Typography>
                </StepLabel>
                <StepContent>
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                </StepContent>
              </Step>
            ))}
          </Stepper>

          {/* Agent Actions Log */}
          <Typography variant="h6" gutterBottom>
            Agent Activity
          </Typography>
          <Paper variant="outlined" sx={{ maxHeight: 200, overflow: 'auto' }}>
            {agentActions.length > 0 ? (
              <List dense>
                <AnimatePresence>
                  {agentActions.slice(-5).map((action, index) => (
                    <motion.div
                      key={`${action.name}-${action.timestamp}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ 
                            bgcolor: getStatusColor(action.status) + '.light',
                            width: 32, 
                            height: 32 
                          }}>
                            {action.status === 'running' && <HourglassEmpty />}
                            {action.status === 'completed' && <CheckCircle />}
                            {action.status === 'failed' && <Error />}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Typography variant="body2" fontWeight="medium">
                              {action.description}
                            </Typography>
                          }
                          secondary={
                            <Box>
                              <Chip 
                                label={action.status}
                                size="small"
                                color={getStatusColor(action.status)}
                                variant="outlined"
                                sx={{ mr: 1, fontSize: '0.7rem' }}
                              />
                              <Typography variant="caption" color="text.secondary">
                                {new Date(action.timestamp).toLocaleTimeString()}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </List>
            ) : (
              <Box p={3} textAlign="center">
                <Typography variant="body2" color="text.secondary">
                  Agent activity will appear here during analysis
                </Typography>
              </Box>
            )}
          </Paper>
        </CardContent>
      </Card>
    </motion.div>
  );
};