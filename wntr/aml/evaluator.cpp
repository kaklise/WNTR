#include "evaluator.hpp"


Evaluator::Evaluator(ExpressionBase* expr)
{
  if (expr->is_leaf())
    {
      Leaf* leaf = dynamic_cast<Leaf*>(expr);
      n_operators = 1;
      n_leaves = 1;
      operators = new short[n_operators];
      arg1_indices = new int[n_operators];
      arg2_indices = new int[n_operators];
      leaves = new Leaf*[1];
      operators[0] = VALUE;
      arg1_indices[0] = 0;
      arg2_indices[0] = 0;
      leaves[0] = leaf;
    }
  else
    {
      Expression* _expr = dynamic_cast<Expression*>(expr);
      n_operators = _expr->num_operators;
      n_leaves = _expr->num_leaves;
      operators = new short[n_operators];
      arg1_indices = new int[n_operators];
      arg2_indices = new int[n_operators];
      leaves = new Leaf*[_expr->num_leaves];

      for (int i=0; i<n_operators; ++i)
	{
	  operators[i] = (*(_expr->operators))[i];
	  arg1_indices[i] = (*(_expr->args1))[i];
	  arg2_indices[i] = (*(_expr->args2))[i];
	}

      Leaf *leaf;
      for (int i=0; i<_expr->num_leaves; ++i)
	{
	  leaf = (*(_expr->leaves))[i];
	  leaves[i] = leaf;
	  if (leaf->is_float())
	    {
	      Float *f = dynamic_cast<Float*>(leaf);
	      f->refcount += 1;
	    }
	}
    }
}


Evaluator::~Evaluator()
{
  Leaf *leaf;
  Float *f;
  for (int i=0; i<n_leaves; ++i)
    {
      leaf = leaves[i];
      if (leaf->is_float())
	{
	  f = dynamic_cast<Float*>(leaf);
	  f->refcount -= 1;
	  if (f->refcount == 0)
	    {
	      delete f;
	    }
	}
    }
  delete operators;
  delete arg1_indices;
  delete arg2_indices;
  delete leaves;
}


void Evaluator::_evaluate(double *values)
{
  short oper;
  int arg1_ndx;
  int arg2_ndx;
  double val1;
  double val2;
  int oper_ndx;
  
  for (int i=0; i<n_operators; ++i)
    {
      oper = operators[i];
      arg1_ndx = arg1_indices[i];
      arg2_ndx = arg2_indices[i];
      if (arg1_ndx >= 0)
	{
	  val1 = leaves[arg1_ndx]->value;
	}
      else
	{
	  oper_ndx = _arg_ndx_to_operator_ndx(arg1_ndx);
	  val1 = values[oper_ndx];
	}
      if (arg2_ndx >= 0)
	{
	  val2 = leaves[arg2_ndx]->value;
	}
      else
	{
	  oper_ndx = _arg_ndx_to_operator_ndx(arg2_ndx);
	  val2 = values[oper_ndx];
	}
      
      if (oper == ADD)
	{
	  values[i] = val1 + val2;
	}
      else if (oper == SUBTRACT)
	{
	  values[i] = val1 - val2;
	}
      else if (oper == VALUE)
	{
	  values[i] = val1;
	}
      else if (oper == MULTIPLY)
	{
	  values[i] = val1 * val2;
	}
      else if (oper == DIVIDE)
	{
	  values[i] = val1 / val2;
	}
      else if (oper == POWER)
	{
	  values[i] = ::pow(val1, val2);
	}
    }
}


double Evaluator::evaluate()
{
  double values[n_operators];
  _evaluate(values);
  return values[n_operators - 1];
}


std::shared_ptr<std::unordered_map<Leaf*, double> > Evaluator::rad()
{
  double values[n_operators];
  _evaluate(values);
  double ders[n_operators];
  short oper;
  int arg1_ndx;
  int arg2_ndx;
  double val1;
  double val2;
  double der;
  double der1;
  double der2;
  int oper_ndx;
  std::shared_ptr<std::unordered_map<Leaf*, double> > res = std::make_shared<std::unordered_map<Leaf*, double> >();
  
  ders[n_operators-1] = 1.0;
  
  for (int i=n_operators-1; i>=0; --i)
    {
      oper = operators[i];
      arg1_ndx = arg1_indices[i];
      arg2_ndx = arg2_indices[i];
      der = ders[i];
      
      if (oper == ADD)
	{
	  der1 = der;
	  der2 = der;
	}
      else if (oper == SUBTRACT)
	{
	  der1 = der;
	  der2 = -der;
	}
      else if (oper == VALUE)
	{
	  der1 = der;
	  der2 = 0.0;
	}
      else if (oper == MULTIPLY)
	{
	  if (arg1_ndx >= 0)
	    {
	      val1 = leaves[arg1_ndx]->value;
	    }
	  else
	    {
	      oper_ndx = _arg_ndx_to_operator_ndx(arg1_ndx);
	      val1 = values[oper_ndx];
	    }
	  if (arg2_ndx >= 0)
	    {
	      val2 = leaves[arg2_ndx]->value;
	    }
	  else
	    {
	      oper_ndx = _arg_ndx_to_operator_ndx(arg2_ndx);
	      val2 = values[oper_ndx];
	    }
	  der1 = der * val2;
	  der2 = der * val1;
	}
      else if (oper == DIVIDE)
	{
	  if (arg1_ndx >= 0)
	    {
	      val1 = leaves[arg1_ndx]->value;
	    }
	  else
	    {
	      oper_ndx = _arg_ndx_to_operator_ndx(arg1_ndx);
	      val1 = values[oper_ndx];
	    }
	  if (arg2_ndx >= 0)
	    {
	      val2 = leaves[arg2_ndx]->value;
	    }
	  else
	    {
	      oper_ndx = _arg_ndx_to_operator_ndx(arg2_ndx);
	      val2 = values[oper_ndx];
	    }
	  der1 = der / val2;
	  der2 = - der * val1 / (val2 * val2);
	}
      else if (oper == POWER)
	{
	  if (arg1_ndx >= 0)
	    {
	      val1 = leaves[arg1_ndx]->value;
	    }
	  else
	    {
	      oper_ndx = _arg_ndx_to_operator_ndx(arg1_ndx);
	      val1 = values[oper_ndx];
	    }
	  if (arg2_ndx >= 0)
	    {
	      val2 = leaves[arg2_ndx]->value;
	    }
	  else
	    {
	      oper_ndx = _arg_ndx_to_operator_ndx(arg2_ndx);
	      val2 = values[oper_ndx];
	    }
	  der1 = der * val2 * ::pow(val1, val2 - 1.0);
	  der2 = der * ::pow(val1, val2) * log(val1);
	}
      
      if (arg1_ndx >= 0)
	{
	  (*res)[leaves[arg1_ndx]] += der1;
	}
      else
	{
	  oper_ndx = _arg_ndx_to_operator_ndx(arg1_ndx);
	  ders[oper_ndx] = der1;
	}
      if (arg2_ndx >= 0)
	{
	  (*res)[leaves[arg2_ndx]] += der2;
	}
      else
	{
	  oper_ndx = _arg_ndx_to_operator_ndx(arg2_ndx);
	  ders[oper_ndx] = der2;
	}
    }
  return res;
}