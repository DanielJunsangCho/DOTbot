/**
 * URL Analysis Form Component
 * Main input interface for DOTbot analysis
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Typography,
  Alert,
  CircularProgress,
  Grid,
  Paper
} from '@mui/material';
import { Search, Psychology, BugReport } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { ScrapeRequest } from '../types/api';

interface UrlAnalysisFormProps {
  onSubmit: (request: ScrapeRequest) => void;
  isLoading: boolean;
  error?: string;
}

const AI_BEHAVIOR_CATEGORIES = [
  'Deceptive Behaviour',
  'Reward Gaming',
  'Sycophancy',
  'Goal Misgeneralization',
  'Unauthorized Access',
  'Proxy Goal Formation',
  'Power Seeking',
  'Social Engineering',
  'Cognitive Off-Policy Behavior',
  'Collusion'
];

export const UrlAnalysisForm: React.FC<UrlAnalysisFormProps> = ({
  onSubmit,
  isLoading,
  error
}) => {
  const [url, setUrl] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  const [maxDepth, setMaxDepth] = useState<number>(2);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) return;

    const request: ScrapeRequest = {
      url: url.trim(),
      question: question.trim() || "What AI behaviors are concerning?",
      // scrape_mode always "auto"
      max_depth: maxDepth,
      categories: categories.length > 0 ? categories : [
        'Deceptive Behaviour',
        'Reward Gaming', 
        'Sycophancy',
        'Goal Misgeneralization',
        'Unauthorized Access'
      ]
    };

    onSubmit(request);
  };

  const handleCategoryToggle = (category: string) => {
    setCategories(prev => 
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card elevation={8} sx={{ maxWidth: 800, mx: 'auto', mb: 4 }}>
        <CardContent sx={{ p: 4 }}>
          <Box display="flex" alignItems="center" mb={3}>
            <Psychology sx={{ fontSize: 24, color: 'text.secondary', mr: 2 }} />
            <Typography variant="h5" component="h1" fontWeight="600" color="text.primary">
              Analysis Configuration
            </Typography>
          </Box>

          <Typography variant="body1" color="text.secondary" mb={4}>
            Analyze websites and content for concerning AI behaviors including deception,
            reward gaming, sycophancy, and goal misgeneralization.
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              {/* URL Input */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Website URL to analyze"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  error={url.length > 0 && !isValidUrl(url)}
                  helperText={
                    url.length > 0 && !isValidUrl(url) 
                      ? "Please enter a valid URL" 
                      : "Enter the URL you want to analyze for AI misalignment"
                  }
                  InputProps={{
                    startAdornment: <Search sx={{ color: 'text.secondary', mr: 1 }} />
                  }}
                />
              </Grid>

              {/* Analysis Question */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Analysis focus (optional)"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="What specific AI behaviors should I look for?"
                  multiline
                  rows={2}
                  helperText="Describe what you're looking for or leave blank for general analysis"
                />
              </Grid>

              {/* Configuration Options - Scraping mode removed, always use "auto" */}

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Analysis Depth</InputLabel>
                  <Select
                    value={maxDepth}
                    label="Analysis Depth"
                    onChange={(e) => setMaxDepth(Number(e.target.value))}
                  >
                    <MenuItem value={1}>Surface Only (Main Page)</MenuItem>
                    <MenuItem value={2}>Deep Analysis (+ Articles)</MenuItem>
                    <MenuItem value={3}>Comprehensive (+ Sub-pages)</MenuItem>
                  </Select>
                </FormControl>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Depth 2+ required for multi-page analysis (recommended for comprehensive results)
                </Typography>
              </Grid>

              {/* AI Behavior Categories */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  AI Behavior Categories to Analyze
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, backgroundColor: 'grey.50' }}>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {AI_BEHAVIOR_CATEGORIES.map((category) => (
                      <Chip
                        key={category}
                        label={category}
                        onClick={() => handleCategoryToggle(category)}
                        color={categories.includes(category) ? 'primary' : 'default'}
                        variant={categories.includes(category) ? 'filled' : 'outlined'}
                        icon={<BugReport />}
                        clickable
                      />
                    ))}
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Select categories to focus on, or leave empty for general analysis
                  </Typography>
                </Paper>
              </Grid>

              {/* Submit Button */}
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={isLoading || !url.trim() || !isValidUrl(url)}
                  sx={{ 
                    py: 1.5,
                    fontSize: '1.1rem',
                    background: 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
                    '&:hover': {
                      background: 'linear-gradient(45deg, #5a67d8 30%, #6b46c1 90%)',
                    }
                  }}
                >
                  {isLoading ? (
                    <>
                      <CircularProgress size={24} sx={{ mr: 2 }} />
                      Analyzing Website...
                    </>
                  ) : (
                    <>
                      <Psychology sx={{ mr: 2 }} />
                      Analyze for AI Misalignment
                    </>
                  )}
                </Button>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>
    </motion.div>
  );
};