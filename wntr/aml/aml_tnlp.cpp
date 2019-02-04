// To build wrapper:
//     swig -c++ -python -builtin aml_core.i
//     python setup.py build_ext --inplace

#include "aml_tnlp.hpp"

using namespace Ipopt;


AML_NLP::AML_NLP()
{}


AML_NLP::~AML_NLP()
{}


bool AML_NLP::get_nlp_info(Index &n, Index &m, Index &nnz_jac_g,
                           Index &nnz_h_lag, TNLP::IndexStyleEnum &index_style)
{
  n = (get_model()->vars).size();
  m = (get_model()->cons).size();
  nnz_jac_g = 0;
  int _con_ndx = 0;
  int _var_ndx = 0;
  for (auto &ptr_to_con : get_model()->cons)
    {
      nnz_jac_g += ptr_to_con->get_vars()->size();
      (get_model()->cons_vector).push_back(ptr_to_con);
      ptr_to_con->index = _con_ndx;
      ++_con_ndx;
    }
  for (auto &ptr_to_var : get_model()->vars)
    {
      (get_model()->vars_vector).push_back(ptr_to_var);
      ptr_to_var->index = _var_ndx;
      ++_var_ndx;
    }
  nnz_h_lag = 0;
  for (auto &row : get_model()->hessian_map)
    {
      for (auto &col : row.second)
        {
	  if (col.first->index <= row.first->index)
	    {
	      assert(col.second["cons"].size() > 0 || col.second["obj"].size() > 0);
	      nnz_h_lag += 1;
	    }
        }
    }
  index_style = TNLP::C_STYLE;
  
  return true;
}


bool AML_NLP::get_bounds_info(Index n, Number *x_l, Number *x_u,
                              Index m, Number *g_l, Number *g_u)
{
  int i = 0;
  for (auto &ptr_to_var : get_model()->vars_vector)
    {
      x_l[i] = ptr_to_var->lb;
      x_u[i] = ptr_to_var->ub;
      ++i;
    }
  
  i = 0;
  for (auto &ptr_to_con : get_model()->cons_vector)
    {
      g_l[i] = ptr_to_con->lb;
      g_u[i] = ptr_to_con->ub;
      ++i;
    }
  
  return true;
}


bool AML_NLP::get_starting_point(Index n, bool init_x, Number *x,
                                 bool init_z, Number *z_L, Number *z_U,
                                 Index m, bool init_lambda,
                                 Number *lambda)
{
  if (init_x)
    {
      int i = 0;
      for (auto &ptr_to_var : get_model()->vars_vector)
        {
	  x[i] = ptr_to_var->value;
	  ++i;
        }
    }
  
  if (init_z)
    {
      int i = 0;
      for (auto &ptr_to_var : get_model()->vars_vector)
        {
	  z_L[i] = ptr_to_var->lb_dual;
	  z_U[i] = ptr_to_var->ub_dual;
	  ++i;
        }
    }
  
  if (init_lambda)
    {
      int i = 0;
      for (auto &ptr_to_con : get_model()->cons_vector)
        {
	  lambda[i] = ptr_to_con->dual;
	  ++i;
        }
    }
  
  return true;
}


bool AML_NLP::eval_f(Index n, const Number *x, bool new_x, Number &obj_value)
{
  if (new_x)
    {
      for (auto &ptr_to_var : get_model()->vars_vector)
        {
	  ptr_to_var->value = x[ptr_to_var->index];
        }
      obj_value = get_model()->obj->evaluate();
      for (auto &ptr_to_con : get_model()->cons_vector)
	{
	  ptr_to_con->evaluate();
	}
    }
  else
    {
      obj_value = get_model()->obj->expr->value;
    }
  
  return true;
}


bool AML_NLP::eval_grad_f(Index n, const Number *x, bool new_x, Number *grad_f)
{
  if (new_x)
    {
      for (auto &ptr_to_var : get_model()->vars_vector)
        {
	  ptr_to_var->value = x[ptr_to_var->index];
        }
      get_model()->obj->evaluate();
      for (auto &ptr_to_con : get_model()->cons_vector)
	{
	  ptr_to_con->evaluate();
	}
    }
  
  for (int i=0; i<n; ++i)
    {
      grad_f[i] = 0.0;
    }
  
  auto obj_vars = get_model()->obj->get_vars();
  for (auto &ptr_to_var : *(obj_vars))
    {
      grad_f[ptr_to_var->index] = get_model()->obj->ad(*ptr_to_var, false);
    }
  
  return true;
}


bool AML_NLP::eval_g(Index n, const Number *x, bool new_x, Index m, Number *g)
{
  if (new_x)
    {
      for (auto &ptr_to_var : get_model()->vars_vector)
        {
	  ptr_to_var->value = x[ptr_to_var->index];
        }
      get_model()->obj->evaluate();
      int i = 0;
      for (auto &ptr_to_con : get_model()->cons_vector)
	{
	  g[i] = ptr_to_con->evaluate();
	  ++i;
	}
    }
  else
    {
      int i = 0;
      for (auto &ptr_to_con : get_model()->cons_vector)
	{
	  g[i] = ptr_to_con->value;
	  ++i;
	}
    }
  return true;
}


bool AML_NLP::eval_jac_g(Index n, const Number *x, bool new_x,
                         Index m, Index nele_jac, Index *iRow, Index *jCol,
                         Number *values)
{
  if (values == NULL)
    {
      int i = 0;
      std::shared_ptr<std::vector<std::shared_ptr<Var> > > con_vars;
      for (auto &ptr_to_con : get_model()->cons_vector)
        {
	  con_vars = ptr_to_con->get_vars();
	  for (auto &ptr_to_var : (*con_vars))
            {
	      iRow[i] = ptr_to_con->index;
	      jCol[i] = ptr_to_var->index;
	      ++i;
            }
        }
      
    }
  else
    {
      if (new_x)
        {
	  for (auto &ptr_to_var : get_model()->vars_vector)
            {
	      ptr_to_var->value = x[ptr_to_var->index];
            }
	  get_model()->obj->evaluate();
	  for (auto &ptr_to_con : get_model()->cons_vector)
	    {
	      ptr_to_con->evaluate();
	    }
        }
      int i = 0;
      std::shared_ptr<std::vector<std::shared_ptr<Var> > > con_vars;
      for (auto &ptr_to_con : get_model()->cons_vector)
        {
	  con_vars = ptr_to_con->get_vars();
	  for (auto &ptr_to_var : (*con_vars))
            {
	      values[i] = ptr_to_con->ad(*ptr_to_var, false);
	      ++i;
            }
        }
    }
  
  return true;
}


bool AML_NLP::eval_h(Index n, const Number *x, bool new_x,
                     Number obj_factor, Index m, const Number *lambda,
                     bool new_lambda, Index nele_hess, Index *iRow,
                     Index *jCol, Number *values)
{
  if (values == NULL)
    {
      int i = 0;
      for (auto &row : get_model()->hessian_map)
        {
	  for (auto &col : row.second)
            {
	      if (col.first->index <= row.first->index)
		{
		  iRow[i] = row.first->index;
		  jCol[i] = col.first->index;
		  ++i;
		  (get_model()->hessian_vector_var1).push_back(row.first);
		  (get_model()->hessian_vector_var2).push_back(col.first);
		}
            }
        }
    }
  else
    {
      if (new_x)
        {
	  for (auto &ptr_to_var : get_model()->vars_vector)
            {
	      ptr_to_var->value = x[ptr_to_var->index];
            }
	  get_model()->obj->evaluate();
	  for (auto &ptr_to_con : get_model()->cons_vector)
	    {
	      ptr_to_con->evaluate();
	    }
        }
      if (new_lambda)
        {
	  for (auto &ptr_to_con : get_model()->cons_vector)
            {
	      ptr_to_con->dual = lambda[ptr_to_con->index];
            }
        }
      int i = 0;
      std::shared_ptr<Var> ptr_to_var2;
      for (auto &ptr_to_var1 : get_model()->hessian_vector_var1)
	{
	  ptr_to_var2 = get_model()->hessian_vector_var2[i];
	  values[i] = 0;
	  for (auto &ptr_to_obj : get_model()->hessian_map[ptr_to_var1][ptr_to_var2]["obj"])
	    {
	      values[i] += obj_factor * ptr_to_obj->ad2(*ptr_to_var1, *ptr_to_var2, false);
	    }
	  for (auto &ptr_to_con : get_model()->hessian_map[ptr_to_var1][ptr_to_var2]["cons"])
	    {
	      values[i] += lambda[ptr_to_con->index] * ptr_to_con->ad2(*ptr_to_var1, *ptr_to_var2, false);
	    }
	  ++i;
	}
    }
  
  return true;
}


void AML_NLP::finalize_solution(SolverReturn status, Index n, const Number *x, const Number *z_L, const Number *z_U,
                                Index m, const Number *g, const Number *lambda, Number obj_value,
                                const IpoptData *ip_data, IpoptCalculatedQuantities *ip_cq)
{
  if (status == SUCCESS)
    {
      get_model()->solver_status = "SUCCESS";
    }
  else if (status == MAXITER_EXCEEDED)
    {
      get_model()->solver_status = "MAXITER_EXCEEDED";
    }
  else if (status == CPUTIME_EXCEEDED)
    {
      get_model()->solver_status = "CPUTIME_EXCEEDED";
    }
  else if (status == STOP_AT_TINY_STEP)
    {
      get_model()->solver_status = "STOP_AT_TINY_STEP";
    }
  else if (status == STOP_AT_ACCEPTABLE_POINT)
    {
      get_model()->solver_status = "STOP_AT_ACCEPTABLE_POINT";
    }
  else if (status == LOCAL_INFEASIBILITY)
    {
      get_model()->solver_status = "LOCAL_INFEASIBILITY";
    }
  else if (status == USER_REQUESTED_STOP)
    {
      get_model()->solver_status = "USER_REQUESTED_STOP";
    }
  else if (status == DIVERGING_ITERATES)
    {
      get_model()->solver_status = "DIVERGING_ITERATES";
    }
  else if (status == RESTORATION_FAILURE)
    {
      get_model()->solver_status = "RESTORATION_FAILURE";
    }
  else if (status == ERROR_IN_STEP_COMPUTATION)
    {
      get_model()->solver_status = "ERROR_IN_STEP_COMPUTATION";
    }
  else if (status == INVALID_NUMBER_DETECTED)
    {
      get_model()->solver_status = "INVALID_NUMBER_DETECTED";
    }
  else if (status == INTERNAL_ERROR)
    {
      get_model()->solver_status = "INTERNAL_ERROR";
    }
  else
    {
      get_model()->solver_status = "UNKNOWN";
    }
  
  for (auto &ptr_to_var : get_model()->vars_vector)
    {
      ptr_to_var->value = x[ptr_to_var->index];
      ptr_to_var->lb_dual = z_L[ptr_to_var->index];
      ptr_to_var->ub_dual = z_U[ptr_to_var->index];
    }
  
  for (auto &ptr_to_con : get_model()->cons_vector)
    {
      ptr_to_con->dual = lambda[ptr_to_con->index];
    }
  (get_model()->vars_vector).clear();
  (get_model()->cons_vector).clear();
  (get_model()->hessian_vector_var1).clear();
  (get_model()->hessian_vector_var2).clear();
}


IpoptModel* AML_NLP::get_model()
{
  return model;
}


void AML_NLP::set_model(IpoptModel *m)
{
  model = m;
}