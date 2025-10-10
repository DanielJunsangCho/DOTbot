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
  Assessment,
  GetApp,
  Link as LinkIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { WorkflowOutput } from '../types/api';

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

const getConfidenceColor = (confidence: number): 'success' | 'warning' | 'error' => {
  if (confidence >= 0.8) return 'error';
  if (confidence >= 0.6) return 'warning';
  return 'success';
};

const getConfidenceLabel = (confidence: number): string => {
  if (confidence >= 0.8) return 'High';
  if (confidence >= 0.6) return 'Medium';
  return 'Low';
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
  const highConfidenceIssues = aiReports.filter(report => report.confidence >= 0.8).length;
  const mediumConfidenceIssues = aiReports.filter(report => report.confidence >= 0.6 && report.confidence < 0.8).length;
  const lowConfidenceIssues = aiReports.filter(report => report.confidence < 0.6).length;

  const averageConfidence = aiReports.length > 0 
    ? aiReports.reduce((sum, report) => sum + report.confidence, 0) / aiReports.length
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

  const downloadAsJSON = () => {
    const dataStr = JSON.stringify(results, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `ai-analysis-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const downloadAsCSV = () => {
    const csvRows = [];
    csvRows.push(['Source', 'Categories', 'Confidence', 'Excerpt', 'Stance', 'Tone', 'Date']);
    
    aiReports.forEach(report => {
      csvRows.push([
        report.source,
        report.categories.join('; '),
        (report.confidence * 100).toFixed(1) + '%',
        `"${report.excerpt.replace(/"/g, '""')}"`,
        report.stance || '',
        report.tone || '',
        report.date || ''
      ]);
    });
    
    const csvContent = csvRows.map(row => row.join(',')).join('\n');
    const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
    const exportFileDefaultName = `ai-analysis-${new Date().toISOString().split('T')[0]}.csv`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const isValidURL = (string: string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
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
            <Box display="flex" gap={1}>
              {results.export_path && (
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={handleDownload}
                  size="small"
                >
                  Download Report
                </Button>
              )}
              <Button
                variant="outlined"
                startIcon={<GetApp />}
                onClick={downloadAsJSON}
                size="small"
              >
                JSON
              </Button>
              <Button
                variant="outlined"
                startIcon={<GetApp />}
                onClick={downloadAsCSV}
                size="small"
                disabled={!hasAIReports}
              >
                CSV
              </Button>
            </Box>
          </Box>

          {/* Summary Alert */}
          {hasAIReports ? (
            <Alert 
              severity={averageConfidence >= 0.8 ? 'error' : averageConfidence >= 0.6 ? 'warning' : 'info'}
              sx={{ mb: 3 }}
              icon={<Psychology />}
            >
              <Typography variant="subtitle1" fontWeight="bold">
                AI Behavior Analysis Complete
              </Typography>
              <Typography variant="body2">
                Found {totalIssues} potential issues across {Object.keys(categoryCount).length} categories.
                Average confidence: {(averageConfidence * 100).toFixed(0)}%
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
                    {highConfidenceIssues}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Confidence
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="warning.main" fontWeight="bold">
                    {mediumConfidenceIssues}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Medium Confidence
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="success.main" fontWeight="bold">
                    {lowConfidenceIssues}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Low Confidence
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
                            color={getConfidenceColor(report.confidence)} 
                            sx={{ mr: 2 }} 
                          />
                          <Box flexGrow={1}>
                            <Typography variant="subtitle1" fontWeight="bold">
                              {report.categories.join(', ')}
                            </Typography>
                            <Box display="flex" alignItems="center" gap={1} mt={1}>
                              <Chip
                                label={`Confidence: ${getConfidenceLabel(report.confidence)}`}
                                color={getConfidenceColor(report.confidence)}
                                size="small"
                              />
                              <Rating
                                value={report.confidence * 5}
                                max={5}
                                size="small"
                                readOnly
                                precision={0.1}
                              />
                              <Chip
                                label={`${(report.confidence * 100).toFixed(0)}%`}
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
                                <strong>Source:</strong>{' '}
                                {isValidURL(report.source) ? (
                                  <Button
                                    component="a"
                                    href={report.source}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    variant="text"
                                    size="small"
                                    startIcon={<LinkIcon />}
                                    sx={{ 
                                      textTransform: 'none',
                                      p: 0,
                                      minWidth: 'auto',
                                      fontSize: 'inherit',
                                      fontWeight: 'normal'
                                    }}
                                  >
                                    {report.source.length > 50 
                                      ? report.source.substring(0, 50) + '...' 
                                      : report.source}
                                  </Button>
                                ) : (
                                  report.source
                                )}
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