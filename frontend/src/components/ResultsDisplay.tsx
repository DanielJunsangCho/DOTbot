/**
 * Results Display Component
 * Shows analysis results with AI behavior detection
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Button,
  Paper,
  Grid,
  Rating,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  Warning,
  CheckCircle,
  BugReport,
  Download,
  ExpandMore,
  Psychology,
  Security,
  TrendingUp,
  Assessment
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { WorkflowOutput, AIBehaviorReport } from '../types/api';

interface ResultsDisplayProps {
  results: WorkflowOutput;
  onDownload?: (exportPath: string) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

const getSeverityColor = (severity: number): 'success' | 'warning' | 'error' => {
  if (severity <= 2) return 'success';
  if (severity <= 3) return 'warning';
  return 'error';
};

const getSeverityLabel = (severity: number): string => {
  if (severity <= 2) return 'Low';
  if (severity <= 3) return 'Medium';
  return 'High';
};

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ 
  results, 
  onDownload 
}) => {
  const [tabValue, setTabValue] = useState(0);

  const aiReports = results.result?.ai_reports || [];
  const structuredData = results.result?.structured_data || [];
  const hasAIReports = aiReports.length > 0;
  const hasStructuredData = structuredData.length > 0;

  // Calculate summary statistics
  const totalIssues = aiReports.length;
  const highSeverityIssues = aiReports.filter(report => report.severity >= 4).length;
  const mediumSeverityIssues = aiReports.filter(report => report.severity === 3).length;
  const lowSeverityIssues = aiReports.filter(report => report.severity <= 2).length;

  const averageSeverity = aiReports.length > 0 
    ? aiReports.reduce((sum, report) => sum + report.severity, 0) / aiReports.length
    : 0;

  const categoryCount = aiReports.reduce((acc, report) => {
    report.categories.forEach(category => {
      acc[category] = (acc[category] || 0) + 1;
    });
    return acc;
  }, {} as Record<string, number>);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleDownload = () => {
    if (results.export_path && onDownload) {
      onDownload(results.export_path);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <Card elevation={6}>
        <CardContent sx={{ p: 4 }}>
          {/* Results Header */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Box>
              <Typography variant="h4" component="h2" gutterBottom>
                Analysis Results
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Analysis completed for: {results.metadata?.url || 'target website'}
              </Typography>
            </Box>
            {results.export_path && (
              <Button
                variant="outlined"
                startIcon={<Download />}
                onClick={handleDownload}
                sx={{ ml: 2 }}
              >
                Download Report
              </Button>
            )}
          </Box>

          {/* Summary Alert */}
          {hasAIReports ? (
            <Alert 
              severity={averageSeverity >= 4 ? 'error' : averageSeverity >= 3 ? 'warning' : 'info'}
              sx={{ mb: 3 }}
              icon={<Psychology />}
            >
              <Typography variant="subtitle1" fontWeight="bold">
                AI Behavior Analysis Complete
              </Typography>
              <Typography variant="body2">
                Found {totalIssues} potential issues across {Object.keys(categoryCount).length} categories.
                Average severity: {averageSeverity.toFixed(1)}/5
              </Typography>
            </Alert>
          ) : (
            <Alert severity="success" sx={{ mb: 3 }} icon={<CheckCircle />}>
              <Typography variant="subtitle1" fontWeight="bold">
                No AI Behaviors Detected
              </Typography>
              <Typography variant="body2">
                The analysis found no significant patterns of concerning AI behavior.
              </Typography>
            </Alert>
          )}

          {/* Summary Statistics */}
          {hasAIReports && (
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={3}>
                <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="error.main" fontWeight="bold">
                    {highSeverityIssues}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Severity
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="warning.main" fontWeight="bold">
                    {mediumSeverityIssues}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Medium Severity
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="success.main" fontWeight="bold">
                    {lowSeverityIssues}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Low Severity
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="primary.main" fontWeight="bold">
                    {Object.keys(categoryCount).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Categories
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          )}

          {/* Tabs for different views */}
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            variant="scrollable"
            scrollButtons="auto"
            sx={{ mb: 2 }}
          >
            <Tab 
              icon={<BugReport />} 
              label="AI Behavior Issues" 
              iconPosition="start"
            />
            <Tab 
              icon={<Assessment />} 
              label="Category Breakdown" 
              iconPosition="start"
            />
            {hasStructuredData && (
              <Tab 
                icon={<TrendingUp />} 
                label="Extracted Data" 
                iconPosition="start"
              />
            )}
          </Tabs>

          <Divider sx={{ mb: 2 }} />

          {/* AI Behavior Issues Tab */}
          <TabPanel value={tabValue} index={0}>
            {hasAIReports ? (
              <List>
                {aiReports.map((report, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <Accordion sx={{ mb: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Box display="flex" alignItems="center" width="100%">
                          <Warning 
                            color={getSeverityColor(report.severity)} 
                            sx={{ mr: 2 }} 
                          />
                          <Box flexGrow={1}>
                            <Typography variant="subtitle1" fontWeight="bold">
                              {report.categories.join(', ')}
                            </Typography>
                            <Box display="flex" alignItems="center" gap={1} mt={1}>
                              <Chip
                                label={`Severity: ${getSeverityLabel(report.severity)}`}
                                color={getSeverityColor(report.severity)}
                                size="small"
                              />
                              <Rating
                                value={report.severity}
                                max={5}
                                size="small"
                                readOnly
                              />
                              <Chip
                                label={`${(report.confidence * 100).toFixed(0)}% confidence`}
                                variant="outlined"
                                size="small"
                              />
                            </Box>
                          </Box>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box>
                          <Typography variant="body1" paragraph>
                            <strong>Evidence:</strong>
                          </Typography>
                          <Paper 
                            variant="outlined" 
                            sx={{ p: 2, backgroundColor: 'grey.50', mb: 2 }}
                          >
                            <Typography variant="body2" style={{ fontStyle: 'italic' }}>
                              "{report.excerpt}"
                            </Typography>
                          </Paper>
                          
                          <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                              <Typography variant="body2">
                                <strong>Source:</strong> {report.source}
                              </Typography>
                              {report.stance && (
                                <Typography variant="body2">
                                  <strong>Stance:</strong> {report.stance}
                                </Typography>
                              )}
                            </Grid>
                            <Grid item xs={12} sm={6}>
                              {report.tone && (
                                <Typography variant="body2">
                                  <strong>Tone:</strong> {report.tone}
                                </Typography>
                              )}
                              {report.date && (
                                <Typography variant="body2">
                                  <strong>Date:</strong> {report.date}
                                </Typography>
                              )}
                            </Grid>
                          </Grid>
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </motion.div>
                ))}
              </List>
            ) : (
              <Box textAlign="center" py={4}>
                <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No AI behaviors detected
                </Typography>
              </Box>
            )}
          </TabPanel>

          {/* Category Breakdown Tab */}
          <TabPanel value={tabValue} index={1}>
            {Object.keys(categoryCount).length > 0 ? (
              <Grid container spacing={2}>
                {Object.entries(categoryCount).map(([category, count]) => (
                  <Grid item xs={12} md={6} key={category}>
                    <Paper elevation={2} sx={{ p: 3 }}>
                      <Box display="flex" alignItems="center" mb={2}>
                        <Security sx={{ mr: 2, color: 'primary.main' }} />
                        <Typography variant="h6" fontWeight="bold">
                          {category}
                        </Typography>
                      </Box>
                      <Typography variant="h3" color="primary.main" fontWeight="bold">
                        {count}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        instances detected
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(count / totalIssues) * 100}
                        sx={{ mt: 2, height: 8, borderRadius: 4 }}
                      />
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Box textAlign="center" py={4}>
                <Typography variant="h6" color="text.secondary">
                  No categories to display
                </Typography>
              </Box>
            )}
          </TabPanel>

          {/* Extracted Data Tab */}
          {hasStructuredData && (
            <TabPanel value={tabValue} index={2}>
              <Typography variant="h6" gutterBottom>
                Extracted Structured Data ({structuredData.length} items)
              </Typography>
              <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
                <List>
                  {structuredData.map((item, index) => (
                    <ListItem key={index} divider>
                      <ListItemIcon>
                        <TrendingUp />
                      </ListItemIcon>
                      <ListItemText
                        primary={item.title || `Data Item ${index + 1}`}
                        secondary={
                          <Typography variant="body2" color="text.secondary">
                            {typeof item === 'string' 
                              ? (item as string).slice(0, 100) + '...'
                              : JSON.stringify(item || {}).slice(0, 100) + '...'
                            }
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </TabPanel>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};